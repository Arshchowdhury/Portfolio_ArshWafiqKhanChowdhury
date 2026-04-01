"""
Document processor — text extraction and token-aware chunking.

Chunk parameters (512 tokens, 20% overlap) are configured in settings.py.
The overlap exists to handle sentences split at chunk boundaries; without it
the semantic ranker occasionally misses relevant passages where the key term
lands at the very end of one chunk and the explanation is at the start of the next.

Limitation: PDF extraction uses PyMuPDF's text layer. Scanned PDFs (image-only)
will produce empty or near-empty chunks and silently produce poor search results.
If the knowledge base includes scanned documents, run them through OCR first or
use Azure AI Document Intelligence before indexing.
"""

import os
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

import fitz  # PyMuPDF
import tiktoken
from docx import Document


ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class DocumentChunk:
    id: str
    title: str
    content: str
    source_url: str
    author: str
    last_modified: str
    chunk_index: int
    total_chunks: int
    token_count: int
    content_vector: list[float] = field(default_factory=list)


def _chunk_text(text: str, chunk_size: int, overlap_ratio: float) -> list[str]:
    """
    Split text into token-bounded chunks with overlap.

    Uses tiktoken for accurate token counting, ensuring chunks stay within
    the configured token limit for embedding model compatibility.
    """
    tokens = ENCODING.encode(text)
    overlap_tokens = int(chunk_size * overlap_ratio)
    step = chunk_size - overlap_tokens

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = ENCODING.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start += step

    return chunks


def _extract_text_from_pdf(path: Path) -> str:
    """Extract full text from a PDF using PyMuPDF."""
    doc = fitz.open(str(path))
    pages = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    return "\n".join(pages)


def _extract_text_from_docx(path: Path) -> str:
    """Extract full text from a DOCX file."""
    doc = Document(str(path))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _generate_chunk_id(source_path: str, chunk_index: int) -> str:
    """Generate a stable, unique ID for each chunk."""
    raw = f"{source_path}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def process_document(
    path: Path,
    chunk_size: int = 512,
    overlap_ratio: float = 0.2,
    author: str = "",
    last_modified: str = "",
    source_url: str = "",
) -> list[DocumentChunk]:
    """
    Process a single document into a list of DocumentChunks.

    Supports PDF and DOCX formats. Returns an empty list if the file
    format is not supported or the file cannot be read.
    """
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text = _extract_text_from_pdf(path)
    elif suffix in (".docx", ".doc"):
        text = _extract_text_from_docx(path)
    else:
        return []

    text = text.strip()
    if not text:
        return []

    raw_chunks = _chunk_text(text, chunk_size, overlap_ratio)
    total = len(raw_chunks)

    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        token_count = len(ENCODING.encode(chunk_text))
        chunk = DocumentChunk(
            id=_generate_chunk_id(str(path), i),
            title=path.stem.replace("_", " ").replace("-", " "),
            content=chunk_text,
            source_url=source_url or str(path),
            author=author,
            last_modified=last_modified,
            chunk_index=i,
            total_chunks=total,
            token_count=token_count,
        )
        chunks.append(chunk)

    return chunks


def process_directory(
    directory: Path,
    chunk_size: int = 512,
    overlap_ratio: float = 0.2,
) -> Generator[DocumentChunk, None, None]:
    """
    Walk a directory and yield DocumentChunks for all supported files.

    Skips hidden files and non-supported formats. Preserves subdirectory
    structure in the source_url field for downstream citation generation.
    """
    for root, _, files in os.walk(directory):
        for filename in sorted(files):
            if filename.startswith("."):
                continue
            path = Path(root) / filename
            if path.suffix.lower() not in (".pdf", ".docx", ".doc"):
                continue
            chunks = process_document(
                path,
                chunk_size=chunk_size,
                overlap_ratio=overlap_ratio,
                source_url=str(path.relative_to(directory)),
            )
            yield from chunks
