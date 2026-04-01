"""Indexer sub-package: document processing and Azure AI Search index management."""

from src.indexer.document_processor import DocumentChunk, process_document, process_directory
from src.indexer.indexer import run_indexing_pipeline
from src.indexer.search_index import create_or_update_index, index_exists

__all__ = [
    "DocumentChunk",
    "process_document",
    "process_directory",
    "run_indexing_pipeline",
    "create_or_update_index",
    "index_exists",
]
