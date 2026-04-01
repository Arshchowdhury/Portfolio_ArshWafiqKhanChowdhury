"""
Unit tests for the document processing and indexing pipeline.

Tests are fully offline — no Azure services are called.
Azure SDK clients are mocked at the boundary to isolate logic.

Run with:
    pytest tests/test_indexer.py -v
"""

import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root so imports resolve without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.indexer.document_processor import (
    DocumentChunk,
    _chunk_text,
    _generate_chunk_id,
    process_document,
)
from src.indexer.indexer import chunks_to_documents, generate_embeddings, _batched


# ---------------------------------------------------------------------------
# _chunk_text
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_short_text_produces_single_chunk(self):
        text = "This is a short sentence."
        chunks = _chunk_text(text, chunk_size=512, overlap_ratio=0.2)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_produces_multiple_chunks(self):
        # ~1200 tokens at chunk_size=512, overlap=0.2 → step=410 → expect 3 chunks
        words = ["governance"] * 600
        text = " ".join(words)
        chunks = _chunk_text(text, chunk_size=512, overlap_ratio=0.2)
        assert len(chunks) >= 2

    def test_chunks_respect_size_limit(self):
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        words = ["policy"] * 800
        text = " ".join(words)
        chunks = _chunk_text(text, chunk_size=512, overlap_ratio=0.2)
        for chunk in chunks:
            token_count = len(enc.encode(chunk))
            assert token_count <= 512, f"Chunk exceeded 512 tokens: {token_count}"

    def test_overlap_creates_shared_tokens(self):
        """Consecutive chunks should share tokens at their boundary."""
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        words = ["word"] * 600
        text = " ".join(words)
        chunks = _chunk_text(text, chunk_size=100, overlap_ratio=0.2)
        assert len(chunks) >= 2

        tokens_0 = enc.encode(chunks[0])
        tokens_1 = enc.encode(chunks[1])
        # Last 20 tokens of chunk 0 should appear at start of chunk 1
        overlap_expected = int(100 * 0.2)
        assert tokens_0[-overlap_expected:] == tokens_1[:overlap_expected]

    def test_empty_text_returns_empty_list(self):
        chunks = _chunk_text("", chunk_size=512, overlap_ratio=0.2)
        assert chunks == []


# ---------------------------------------------------------------------------
# _generate_chunk_id
# ---------------------------------------------------------------------------

class TestGenerateChunkId:
    def test_id_is_md5_hex_string(self):
        chunk_id = _generate_chunk_id("some/path/doc.pdf", 0)
        assert len(chunk_id) == 32
        assert all(c in "0123456789abcdef" for c in chunk_id)

    def test_same_inputs_produce_same_id(self):
        id1 = _generate_chunk_id("docs/policy.pdf", 3)
        id2 = _generate_chunk_id("docs/policy.pdf", 3)
        assert id1 == id2

    def test_different_chunk_index_produces_different_id(self):
        id0 = _generate_chunk_id("docs/policy.pdf", 0)
        id1 = _generate_chunk_id("docs/policy.pdf", 1)
        assert id0 != id1

    def test_different_path_produces_different_id(self):
        id_a = _generate_chunk_id("docs/policy_a.pdf", 0)
        id_b = _generate_chunk_id("docs/policy_b.pdf", 0)
        assert id_a != id_b

    def test_id_is_deterministic_and_matches_expected(self):
        raw = "docs/policy.pdf::0"
        expected = hashlib.md5(raw.encode()).hexdigest()
        assert _generate_chunk_id("docs/policy.pdf", 0) == expected


# ---------------------------------------------------------------------------
# process_document
# ---------------------------------------------------------------------------

class TestProcessDocument:
    def test_unsupported_format_returns_empty_list(self, tmp_path):
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("Some notes.")
        chunks = process_document(txt_file)
        assert chunks == []

    def test_pdf_processing(self, tmp_path):
        """Test PDF processing with a minimal real PDF using fitz."""
        import fitz

        pdf_path = tmp_path / "test_doc.pdf"
        doc = fitz.open()
        page = doc.new_page()
        # Insert enough text to produce at least one chunk
        page.insert_text((72, 72), "AI governance policy. " * 50)
        doc.save(str(pdf_path))
        doc.close()

        chunks = process_document(pdf_path, chunk_size=512, overlap_ratio=0.2)
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)
        assert chunks[0].title == "test doc"  # underscores replaced with spaces
        assert chunks[0].chunk_index == 0
        assert chunks[-1].chunk_index == len(chunks) - 1
        assert chunks[0].total_chunks == len(chunks)

    def test_docx_processing(self, tmp_path):
        """Test DOCX processing with a minimal real DOCX."""
        from docx import Document as DocxDocument

        docx_path = tmp_path / "governance_policy.docx"
        doc = DocxDocument()
        # Write enough content for at least one chunk
        for _ in range(20):
            doc.add_paragraph("The AI governance framework requires organisations to. " * 10)
        doc.save(str(docx_path))

        chunks = process_document(docx_path, chunk_size=512, overlap_ratio=0.2)
        assert len(chunks) >= 1
        assert chunks[0].title == "governance policy"

    def test_chunk_ids_are_unique(self, tmp_path):
        import fitz

        pdf_path = tmp_path / "multi_chunk.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Policy content. " * 400)
        doc.save(str(pdf_path))
        doc.close()

        chunks = process_document(pdf_path, chunk_size=128, overlap_ratio=0.2)
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs are not unique"


# ---------------------------------------------------------------------------
# chunks_to_documents
# ---------------------------------------------------------------------------

class TestChunksToDocuments:
    def _make_chunk(self, idx: int = 0) -> DocumentChunk:
        return DocumentChunk(
            id=f"abc{idx}",
            title="Test Policy",
            content="Some governance content.",
            source_url="policies/test.pdf",
            author="",
            last_modified="",
            chunk_index=idx,
            total_chunks=2,
            token_count=4,
            content_vector=[0.1, 0.2, 0.3],
        )

    def test_converts_to_expected_dict_shape(self):
        chunk = self._make_chunk(0)
        docs = chunks_to_documents([chunk])
        assert len(docs) == 1
        d = docs[0]
        assert d["id"] == "abc0"
        assert d["title"] == "Test Policy"
        assert d["content"] == "Some governance content."
        assert d["sourceUrl"] == "policies/test.pdf"
        assert d["chunkIndex"] == 0
        assert d["totalChunks"] == 2
        assert d["contentVector"] == [0.1, 0.2, 0.3]

    def test_empty_last_modified_maps_to_none(self):
        chunk = self._make_chunk()
        docs = chunks_to_documents([chunk])
        assert docs[0]["lastModified"] is None


# ---------------------------------------------------------------------------
# _batched
# ---------------------------------------------------------------------------

class TestBatched:
    def test_exact_multiple(self):
        items = list(range(10))
        batches = list(_batched(items, 5))
        assert batches == [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

    def test_remainder(self):
        items = list(range(7))
        batches = list(_batched(items, 3))
        assert batches == [[0, 1, 2], [3, 4, 5], [6]]

    def test_empty_input(self):
        assert list(_batched([], 10)) == []

    def test_batch_larger_than_input(self):
        items = [1, 2]
        batches = list(_batched(items, 100))
        assert batches == [[1, 2]]


# ---------------------------------------------------------------------------
# generate_embeddings (mocked)
# ---------------------------------------------------------------------------

class TestGenerateEmbeddings:
    def test_returns_embeddings_matching_input_count(self):
        mock_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1536

        mock_client.embeddings.create.return_value = MagicMock(
            data=[mock_embedding, mock_embedding]
        )

        texts = ["query one", "query two"]
        result = generate_embeddings(texts, mock_client)

        assert len(result) == 2
        assert result[0] == [0.1] * 1536

    def test_retries_on_rate_limit(self):
        mock_client = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.5] * 1536

        # First call raises 429, second succeeds
        mock_client.embeddings.create.side_effect = [
            Exception("429 Too Many Requests"),
            MagicMock(data=[mock_embedding]),
        ]

        with patch("scripts.run_indexer.time.sleep") as mock_sleep, \
             patch("src.indexer.indexer.time.sleep") as mock_sleep2:
            result = generate_embeddings(["test text"], mock_client)

        assert len(result) == 1

    def test_non_rate_limit_exception_propagates(self):
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("500 Internal Server Error")

        with pytest.raises(Exception, match="500 Internal Server Error"):
            generate_embeddings(["text"], mock_client)
