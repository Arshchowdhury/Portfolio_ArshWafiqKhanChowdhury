"""
retrieve.py — FindField Query Assistant
Hybrid retrieval: vector search + semantic ranking.

This module queries Azure AI Search using a hybrid strategy:
  1. Vector search — finds semantically similar chunks via embedding similarity
  2. Keyword search — finds chunks with exact or fuzzy term matches
  3. Semantic reranking — reranks combined results by relevance to query intent

The hybrid approach outperforms either method alone because:
  - Vector search handles paraphrased and intent-based queries
  - Keyword search handles exact terms (policy IDs, product names)
  - Semantic reranking resolves conflicts between the two

Author: Arsh Wafiq Khan Chowdhury
"""

import logging
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery,
    SemanticSearchOptions,
    SemanticQuery,
)
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    """A single retrieved document chunk."""
    chunk_id: str
    content: str
    source_document: str
    category: str
    effective_date: str
    audience: str
    chunk_index: int
    page_number: int
    score: float                   # Reranker score (0–4 scale from semantic ranker)
    reranker_score: float          # Raw semantic reranker score
    highlights: list[str]          # Highlighted matching passages


# ── Retrieval Engine ─────────────────────────────────────────────────────────

class RetrievalEngine:
    """
    Hybrid retrieval engine for the FindField RAG pipeline.

    Usage:
        engine = RetrievalEngine(config)
        results = engine.retrieve("What is the late payment penalty?")
        for r in results:
            print(r.content, r.source_document)
    """

    def __init__(self, config: Config):
        self.config = config
        self.credential = DefaultAzureCredential()

        self.search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=self.credential,
        )
        self.openai_client = AzureOpenAI(
            azure_endpoint=config.openai_endpoint,
            azure_ad_token_provider=self._get_token,
            api_version=config.openai_api_version,
        )

    def _get_token(self) -> str:
        return self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token

    def retrieve(
        self,
        query: str,
        audience: str = "customer",
        category_filter: str = None,
        top_k: int = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Args:
            query: Natural language query from the user
            audience: Filter to "customer" or "internal" documents.
                      Customer-facing agent must never surface internal docs.
            category_filter: Optionally restrict to a specific document category
            top_k: Override the config default for top-k results

        Returns:
            List of RetrievalResult objects, ranked by relevance.
        """
        k = top_k or self.config.top_k_results
        query_embedding = self._embed_query(query)

        # Build OData filter
        # Audience filter is always applied — security requirement.
        # Category filter is optional, used for domain-scoped queries.
        filters = [f"audience eq '{audience}'"]
        if category_filter:
            filters.append(f"category eq '{category_filter}'")
        odata_filter = " and ".join(filters)

        # ── Hybrid Search ──────────────────────────────────────────────────
        # VectorizedQuery: finds semantically similar chunks
        # search_text: keyword search over the content field
        # QueryType.SEMANTIC + SemanticSearchOptions: reranks results
        #
        # Design decision: exhaustive=True on VectorizedQuery disables HNSW
        # approximation for queries — uses brute-force exact search.
        # For 400 documents (~2,000 chunks), brute-force is fast enough
        # (<50ms) and gives better recall than approximate search.
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=k * 3,      # Retrieve 3x candidates for reranker
            fields="contentVector",
            exhaustive=True,
        )

        response = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=odata_filter,
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name="findfield-semantic-config",
            semantic_query=SemanticQuery(query=query),
            highlight_fields="content",
            top=k,
            select=[
                "id", "content", "sourceDocument", "category",
                "effectiveDate", "audience", "chunkIndex", "pageNumber",
            ],
        )

        results = []
        for hit in response:
            score = hit.get("@search.score", 0.0)
            reranker_score = hit.get("@search.reranker_score", 0.0)

            # Filter by minimum score threshold
            # Chunks below threshold are noise — better to return nothing
            # than to return an irrelevant answer with false confidence.
            if score < self.config.min_score_threshold:
                continue

            highlights = []
            if hit.get("@search.highlights"):
                highlights = hit["@search.highlights"].get("content", [])

            results.append(RetrievalResult(
                chunk_id=hit["id"],
                content=hit["content"],
                source_document=hit["sourceDocument"],
                category=hit["category"],
                effective_date=hit["effectiveDate"],
                audience=hit["audience"],
                chunk_index=hit["chunkIndex"],
                page_number=hit["pageNumber"],
                score=score,
                reranker_score=reranker_score,
                highlights=highlights,
            ))

        logger.info(
            f"Retrieved {len(results)} chunks for query: "
            f"'{query[:60]}...' (audience={audience})"
        )
        return results

    def format_context(self, results: list[RetrievalResult]) -> str:
        """
        Format retrieved chunks into the context string for the LLM prompt.

        Each chunk is labelled with its source for the citation requirement.
        Chunks are ordered by reranker score (highest first).
        """
        if not results:
            return "No relevant documents found."

        sorted_results = sorted(results, key=lambda r: r.reranker_score, reverse=True)

        context_parts = []
        for i, r in enumerate(sorted_results, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Source: {r.source_document} (effective {r.effective_date})\n"
                f"Category: {r.category}\n"
                f"Content:\n{r.content}"
            )

        return "\n\n---\n\n".join(context_parts)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _embed_query(self, query: str) -> list[float]:
        """Embed a user query for vector search."""
        response = self.openai_client.embeddings.create(
            model=self.config.openai_embedding_deployment,
            input=query,
        )
        return response.data[0].embedding
