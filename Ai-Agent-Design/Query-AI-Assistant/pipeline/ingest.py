"""
ingest.py — FindField Query Assistant
Document ingestion pipeline: chunk → embed → index.

This module:
  1. Downloads documents from Azure Blob Storage
  2. Extracts text from PDF and DOCX files
  3. Chunks text into overlapping windows (token-aware)
  4. Generates embeddings via Azure OpenAI text-embedding-3-large
  5. Upserts chunks into Azure AI Search vector index

Design decisions documented inline.

Author: Arsh Wafiq Khan Chowdhury
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import tiktoken
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import IndexDocumentsBatch
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI
from pypdf import PdfReader
from docx import Document as DocxDocument
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from config import Config

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class DocumentChunk:
    """A single chunk of text ready for indexing."""
    id: str                        # Deterministic: hash(source_doc + chunk_index)
    content: str                   # The chunk text
    content_vector: list[float]    # 3072-dim embedding from text-embedding-3-large
    source_document: str           # Original filename
    category: str                  # Document category from blob metadata
    effective_date: str            # ISO date from blob metadata
    audience: str                  # "customer" | "internal"
    chunk_index: int               # Position within source document
    page_number: int               # Approximate page number


@dataclass
class IngestionResult:
    """Summary of a single ingestion run."""
    documents_processed: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    failed_documents: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


# ── Ingestion Pipeline ───────────────────────────────────────────────────────

class IngestionPipeline:
    """
    Orchestrates the full document ingestion flow.

    Usage:
        config = load_config()
        pipeline = IngestionPipeline(config)
        result = pipeline.run()
    """

    def __init__(self, config: Config):
        self.config = config
        self.credential = DefaultAzureCredential()

        # Azure clients — all using Managed Identity (no API keys)
        self.blob_client = BlobServiceClient(
            account_url=f"https://{config.storage_account_name}.blob.core.windows.net",
            credential=self.credential,
        )
        self.search_client = SearchClient(
            endpoint=config.search_endpoint,
            index_name=config.search_index_name,
            credential=self.credential,
        )
        self.openai_client = AzureOpenAI(
            azure_endpoint=config.openai_endpoint,
            azure_ad_token_provider=self._get_openai_token,
            api_version=config.openai_api_version,
        )

        # Tokeniser for chunk size management
        # cl100k_base is the encoding used by text-embedding-3-large
        self.tokeniser = tiktoken.get_encoding("cl100k_base")

    def _get_openai_token(self) -> str:
        """Token provider for Azure OpenAI — uses Managed Identity."""
        return self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token

    def run(self, category_filter: str = None) -> IngestionResult:
        """
        Run the full ingestion pipeline.

        Args:
            category_filter: If set, only process blobs with this category tag.
                             Useful for incremental updates (e.g., only re-index
                             "policy" documents when policy library changes).
        """
        start = datetime.now(timezone.utc)
        result = IngestionResult()

        container = self.blob_client.get_container_client(
            self.config.storage_container_name
        )

        blobs = list(container.list_blobs(include=["metadata"]))
        if category_filter:
            blobs = [b for b in blobs if b.metadata.get("category") == category_filter]

        logger.info(f"Processing {len(blobs)} documents")

        all_chunks: list[DocumentChunk] = []

        for blob in tqdm(blobs, desc="Processing documents"):
            try:
                chunks = self._process_blob(container, blob)
                all_chunks.extend(chunks)
                result.documents_processed += 1
                result.chunks_created += len(chunks)
            except Exception as e:
                logger.error(f"Failed to process {blob.name}: {e}")
                result.failed_documents.append(blob.name)

        # Batch index all chunks
        # Batching in groups of 100 balances throughput and error isolation.
        # If one batch fails, only 100 chunks need reprocessing, not everything.
        indexed = self._batch_index(all_chunks)
        result.chunks_indexed = indexed
        result.duration_seconds = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        logger.info(
            f"Ingestion complete: {result.documents_processed} docs, "
            f"{result.chunks_indexed} chunks indexed in {result.duration_seconds:.1f}s"
        )
        return result

    def _process_blob(self, container, blob) -> list[DocumentChunk]:
        """Download, extract, chunk, and embed a single blob."""

        # Download
        data = container.download_blob(blob.name).readall()

        # Extract text based on file type
        suffix = Path(blob.name).suffix.lower()
        if suffix == ".pdf":
            text = self._extract_pdf(data)
        elif suffix in (".docx", ".doc"):
            text = self._extract_docx(data)
        elif suffix == ".txt":
            text = data.decode("utf-8", errors="ignore")
        else:
            logger.warning(f"Unsupported file type: {blob.name}, skipping")
            return []

        if not text.strip():
            logger.warning(f"No text extracted from {blob.name}")
            return []

        # Chunk
        raw_chunks = list(self._chunk_text(text))

        # Get metadata from blob tags
        metadata = blob.metadata or {}
        category = metadata.get("category", "general")
        effective_date = metadata.get("effective_date", datetime.now().date().isoformat())
        audience = metadata.get("audience", "internal")

        # Embed and build DocumentChunk objects
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            embedding = self._embed(chunk_text)
            chunk_id = hashlib.sha256(
                f"{blob.name}:{i}".encode()
            ).hexdigest()[:32]

            chunks.append(DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                content_vector=embedding,
                source_document=blob.name,
                category=category,
                effective_date=effective_date,
                audience=audience,
                chunk_index=i,
                page_number=self._estimate_page(i, len(raw_chunks)),
            ))

        return chunks

    def _extract_pdf(self, data: bytes) -> str:
        """Extract text from PDF bytes."""
        import io
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)

    def _extract_docx(self, data: bytes) -> str:
        """Extract text from DOCX bytes."""
        import io
        doc = DocxDocument(io.BytesIO(data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    def _chunk_text(self, text: str) -> Iterator[str]:
        """
        Split text into overlapping token-aware chunks.

        Design decision: Token-aware chunking (vs character-based) ensures
        chunks stay within the embedding model's context window and avoids
        cutting mid-sentence at arbitrary character positions.

        Overlap of 64 tokens ensures context continuity — answers that span
        chunk boundaries are still retrievable because adjacent chunks share
        context.
        """
        tokens = self.tokeniser.encode(text)
        chunk_size = self.config.chunk_size_tokens
        overlap = self.config.chunk_overlap_tokens

        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokeniser.decode(chunk_tokens)

            # Only yield chunks with meaningful content
            if len(chunk_text.strip()) > 50:
                yield chunk_text

            if end == len(tokens):
                break
            start = end - overlap  # Slide window with overlap

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _embed(self, text: str) -> list[float]:
        """
        Generate embedding for a text chunk.

        Using text-embedding-3-large (3072 dimensions) rather than
        text-embedding-ada-002 (1536 dimensions) for higher retrieval
        accuracy on policy/procedure content where semantic nuance matters.

        Retry decorator handles transient API rate limit errors —
        essential for batch processing 400+ documents.
        """
        response = self.openai_client.embeddings.create(
            model=self.config.openai_embedding_deployment,
            input=text,
        )
        return response.data[0].embedding

    def _batch_index(self, chunks: list[DocumentChunk]) -> int:
        """Upload chunks to Azure AI Search in batches of 100."""
        indexed = 0
        batch_size = 100

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            documents = [
                {
                    "id": c.id,
                    "content": c.content,
                    "contentVector": c.content_vector,
                    "sourceDocument": c.source_document,
                    "category": c.category,
                    "effectiveDate": c.effective_date,
                    "audience": c.audience,
                    "chunkIndex": c.chunk_index,
                    "pageNumber": c.page_number,
                }
                for c in batch
            ]
            result = self.search_client.upload_documents(documents=documents)
            indexed += sum(1 for r in result if r.succeeded)

        return indexed

    def _estimate_page(self, chunk_index: int, total_chunks: int) -> int:
        """Approximate page number based on chunk position."""
        # Assumes ~4 chunks per page on average (reasonable for A4 policy docs)
        return max(1, chunk_index // 4 + 1)


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from config import load_config

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="FindField document ingestion pipeline")
    parser.add_argument("--category", help="Only ingest documents with this category tag")
    parser.add_argument("--key-vault", help="Key Vault URL for production config")
    args = parser.parse_args()

    config = load_config(
        use_key_vault=bool(args.key_vault),
        key_vault_url=args.key_vault,
    )

    pipeline = IngestionPipeline(config)
    result = pipeline.run(category_filter=args.category)

    print(json.dumps({
        "documents_processed": result.documents_processed,
        "chunks_created": result.chunks_created,
        "chunks_indexed": result.chunks_indexed,
        "failed_documents": result.failed_documents,
        "duration_seconds": result.duration_seconds,
    }, indent=2))
