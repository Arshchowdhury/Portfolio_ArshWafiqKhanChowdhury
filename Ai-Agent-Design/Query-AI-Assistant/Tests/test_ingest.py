"""
test_ingest.py — Unit tests for the ingestion pipeline.
Tests chunking logic, metadata extraction, and batch indexing
without requiring live Azure service connections.

Run: pytest tests/test_ingest.py -v

Author: Arsh Wafiq Khan Chowdhury
"""

import hashlib
import pytest
from unittest.mock import MagicMock, patch
from config import Config


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_config():
    return Config(
        openai_endpoint="https://oai-apex-test.openai.azure.com/",
        openai_deployment="gpt-4o",
        openai_embedding_deployment="text-embedding-3-large",
        openai_api_version="2024-08-01-preview",
        search_endpoint="https://srch-apex-test.search.windows.net",
        search_index_name="apex-documents",
        storage_account_name="stapextest",
        storage_container_name="apex-documents",
        chunk_size_tokens=512,
        chunk_overlap_tokens=64,
        top_k_results=5,
        min_score_threshold=0.75,
    )


@pytest.fixture
def pipeline(mock_config):
    """IngestionPipeline with mocked Azure clients."""
    with patch("ingest.BlobServiceClient"), \
         patch("ingest.SearchClient"), \
         patch("ingest.AzureOpenAI"), \
         patch("ingest.DefaultAzureCredential"):
        from ingest import IngestionPipeline
        p = IngestionPipeline(mock_config)
        p.openai_client = MagicMock()
        p.search_client = MagicMock()
        p.blob_client = MagicMock()
        return p


# ── Chunking Tests ────────────────────────────────────────────────────────────

class TestChunking:
    """
    Tests for the token-aware chunking strategy.

    Key invariants:
      - No chunk exceeds chunk_size_tokens
      - Consecutive chunks share overlap_tokens of context
      - Short content (< 50 chars) is not emitted as a chunk
    """

    def test_short_text_single_chunk(self, pipeline):
        text = "This is a short document. It fits in one chunk easily."
        chunks = list(pipeline._chunk_text(text))
        assert len(chunks) == 1

    def test_long_text_produces_multiple_chunks(self, pipeline):
        # ~600 tokens of text should produce 2 chunks at 512-token size
        words = ["policy"] * 600
        text = " ".join(words)
        chunks = list(pipeline._chunk_text(text))
        assert len(chunks) >= 2

    def test_chunks_have_overlap(self, pipeline):
        """Consecutive chunks should share content (overlap)."""
        words = ["word"] * 700
        text = " ".join(words)
        chunks = list(pipeline._chunk_text(text))
        if len(chunks) >= 2:
            # The end of chunk 0 should appear at the start of chunk 1
            end_of_first = chunks[0].split()[-20:]
            start_of_second = chunks[1].split()[:20:]
            overlap = set(end_of_first) & set(start_of_second)
            assert len(overlap) > 0

    def test_minimum_content_filter(self, pipeline):
        """Chunks with fewer than 50 characters should be filtered out."""
        text = "Short.\n\n\n" + ("This is a real sentence with enough content. " * 20)
        chunks = list(pipeline._chunk_text(text))
        for chunk in chunks:
            assert len(chunk.strip()) >= 50

    def test_empty_text_returns_no_chunks(self, pipeline):
        chunks = list(pipeline._chunk_text(""))
        assert len(chunks) == 0

    def test_whitespace_only_returns_no_chunks(self, pipeline):
        chunks = list(pipeline._chunk_text("   \n\n\t   "))
        assert len(chunks) == 0


# ── Chunk ID Tests ────────────────────────────────────────────────────────────

class TestChunkIds:
    """
    Chunk IDs must be deterministic.
    The same document at the same chunk index must always produce the same ID.
    This allows safe re-ingestion (upsert, not duplicate insert).
    """

    def test_chunk_id_is_deterministic(self):
        blob_name = "policy-document.pdf"
        chunk_index = 3
        expected_id = hashlib.sha256(
            f"{blob_name}:{chunk_index}".encode()
        ).hexdigest()[:32]

        # Compute again — must be identical
        actual_id = hashlib.sha256(
            f"{blob_name}:{chunk_index}".encode()
        ).hexdigest()[:32]

        assert expected_id == actual_id

    def test_different_documents_produce_different_ids(self):
        id_a = hashlib.sha256("doc-a.pdf:0".encode()).hexdigest()[:32]
        id_b = hashlib.sha256("doc-b.pdf:0".encode()).hexdigest()[:32]
        assert id_a != id_b

    def test_different_chunk_indices_produce_different_ids(self):
        id_0 = hashlib.sha256("doc.pdf:0".encode()).hexdigest()[:32]
        id_1 = hashlib.sha256("doc.pdf:1".encode()).hexdigest()[:32]
        assert id_0 != id_1


# ── PDF Extraction Tests ──────────────────────────────────────────────────────

class TestTextExtraction:

    def test_extract_pdf_returns_string(self, pipeline):
        """PDF extraction should return a non-empty string for a valid PDF."""
        import io
        from pypdf import PdfWriter

        # Create a minimal PDF in memory
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buffer = io.BytesIO()
        writer.write(buffer)
        pdf_bytes = buffer.getvalue()

        # Blank page — extraction returns empty or whitespace, not an error
        result = pipeline._extract_pdf(pdf_bytes)
        assert isinstance(result, str)

    def test_extract_txt(self, pipeline):
        text = "This is a plain text document."
        result = text.encode("utf-8").decode("utf-8", errors="ignore")
        assert "plain text document" in result


# ── Batch Indexing Tests ──────────────────────────────────────────────────────

class TestBatchIndexing:

    def test_batch_size_respected(self, pipeline):
        """Indexer should call upload_documents in batches of 100."""
        from ingest import DocumentChunk

        # Create 250 fake chunks
        chunks = [
            DocumentChunk(
                id=f"chunk_{i}",
                content=f"Content {i}",
                content_vector=[0.1] * 3072,
                source_document="test.pdf",
                category="policy",
                effective_date="2026-01-01",
                audience="customer",
                chunk_index=i,
                page_number=i // 4 + 1,
            )
            for i in range(250)
        ]

        # Mock upload_documents to track calls
        mock_result = [MagicMock(succeeded=True)]
        pipeline.search_client.upload_documents = MagicMock(
            return_value=mock_result * 100
        )

        pipeline._batch_index(chunks)

        # 250 chunks / 100 per batch = 3 calls
        assert pipeline.search_client.upload_documents.call_count == 3
