"""
RAG query engine — see docs/02_Solution_Design_Document.md for architecture context.

Confidence bands (based on semantic reranker score):
  High:       >= 0.85
  Medium:     0.70 – 0.84
  Escalated:  < 0.70  (returns escalation signal, no generated response)

The 0.7 threshold came out of UAT testing. Lower values produced responses
that were technically grounded but drew on tangentially related chunks,
which the legal/risk reviewers flagged as misleading. Better to escalate
than to confidently answer from weak evidence.
"""

from dataclasses import dataclass
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
)
from openai import AzureOpenAI

from config.settings import settings


SYSTEM_PROMPT = """You are the AI Governance Advisory Agent for Meridian Advisory Group.
Your role is to answer questions about AI governance regulations, internal AI policies,
and AI risk management frameworks.

Answer only from the provided source documents — do not draw on outside knowledge.
Cite sources inline using [Source: <document title>] after each key claim.
If the documents do not contain enough information to answer, say so directly rather
than inferring or extrapolating.

Your audience is legal, risk, and strategy professionals. Be precise. Avoid hedging
with phrases like "it depends" unless you explain what it depends on and where that
nuance appears in the source material.

Do not speculate about regulatory interpretations that are not explicitly stated in
the provided documents.
"""


@dataclass
class Citation:
    title: str
    source_url: str
    chunk_index: int


@dataclass
class QueryResult:
    query: str
    response: str
    citations: list[Citation]
    confidence_band: str  # "High", "Medium", or "Escalated"
    top_score: float
    escalated: bool
    session_id: str


def _confidence_band(score: float) -> str:
    if score >= 0.85:
        return "High"
    elif score >= 0.70:
        return "Medium"
    return "Escalated"


def _build_context(search_results: list[dict]) -> tuple[str, list[Citation]]:
    """
    Build a context string and citation list from search results.

    Each document chunk is prefixed with its title and chunk index so the
    language model can reference it in citations.
    """
    context_parts = []
    citations = []

    for i, result in enumerate(search_results):
        title = result.get("title", "Unknown")
        content = result.get("content", "")
        source_url = result.get("sourceUrl", "")
        chunk_index = result.get("chunkIndex", 0)

        context_parts.append(
            f"[Document {i + 1}: {title} (chunk {chunk_index})]\n{content}"
        )
        citations.append(
            Citation(title=title, source_url=source_url, chunk_index=chunk_index)
        )

    return "\n\n---\n\n".join(context_parts), citations


class QueryEngine:
    def __init__(self):
        self._search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=settings.azure_search_index_name,
            credential=AzureKeyCredential(settings.azure_search_key),
        )
        self._openai_client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_key,
            api_version=settings.azure_openai_api_version,
        )

    def _embed_query(self, query: str) -> list[float]:
        response = self._openai_client.embeddings.create(
            model=settings.azure_openai_embedding_deployment,
            input=query,
        )
        return response.data[0].embedding

    def _hybrid_search(self, query: str, query_vector: list[float]) -> list[dict]:
        """
        Run a hybrid search combining BM25 keyword retrieval and vector search,
        fused via RRF, then re-ranked by the semantic ranker.

        Only returns results with a reranker score >= confidence_threshold.
        """
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=settings.top_k_results,
            fields="contentVector",
        )

        results = self._search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name=settings.semantic_config_name,
            query_caption=QueryCaptionType.EXTRACTIVE,
            query_answer=QueryAnswerType.EXTRACTIVE,
            top=settings.top_k_results,
            select=["id", "title", "content", "sourceUrl", "chunkIndex", "totalChunks"],
        )

        qualified = []
        for result in results:
            score = result.get("@search.reranker_score") or 0.0
            if score >= settings.confidence_threshold:
                result_dict = dict(result)
                result_dict["_reranker_score"] = score
                qualified.append(result_dict)

        return qualified

    def _generate_response(self, query: str, context: str) -> str:
        """Generate a grounded response using GPT-4o with the retrieved context."""
        user_message = (
            f"Context documents:\n\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer based only on the context documents above. "
            "Cite the source document for each key claim."
        )

        completion = self._openai_client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,  # Low temperature for factual, grounded responses
            max_tokens=1000,
        )

        return completion.choices[0].message.content

    def query(self, user_query: str, session_id: str = "") -> QueryResult:
        """
        Process a governance query end-to-end.

        Returns a QueryResult with the generated response and citations if
        qualifying documents are found, or an escalation signal if no documents
        meet the confidence threshold.
        """
        query_vector = self._embed_query(user_query)
        search_results = self._hybrid_search(user_query, query_vector)

        if not search_results:
            return QueryResult(
                query=user_query,
                response=(
                    "I was unable to find source documents with sufficient confidence "
                    "to answer this query. This question has been escalated to the "
                    "AI Practice team, who will respond within one business day."
                ),
                citations=[],
                confidence_band="Escalated",
                top_score=0.0,
                escalated=True,
                session_id=session_id,
            )

        # Confidence band is derived from the top result only, not the average.
        # Using the average smoothed over low-quality tail results in UAT and
        # caused queries to appear Medium-confidence when the second/third chunks
        # were only marginally above threshold.
        top_score = search_results[0].get("_reranker_score", 0.0)
        context, citations = _build_context(search_results)
        response_text = self._generate_response(user_query, context)

        return QueryResult(
            query=user_query,
            response=response_text,
            citations=citations,
            confidence_band=_confidence_band(top_score),
            top_score=top_score,
            escalated=False,
            session_id=session_id,
        )
