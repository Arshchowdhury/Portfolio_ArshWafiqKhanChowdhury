"""
Document indexing entry point.

Runs the full indexing pipeline against the knowledge-base directory:
  1. Ensures the Azure AI Search index exists (creates it if not)
  2. Walks the knowledge-base directory, extracts text from PDF and DOCX files
  3. Splits extracted text into 512-token chunks with 20% overlap
  4. Generates text-embedding-ada-002 embeddings for each chunk (batched)
  5. Uploads all chunk documents to Azure AI Search

Intended usage:
  # Index using the default knowledge-base/ directory
  python scripts/run_indexer.py

  # Index a custom directory
  python scripts/run_indexer.py --path /path/to/documents

  # Dry run: count documents without uploading
  python scripts/run_indexer.py --dry-run
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path so config and src imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console

from config.settings import settings
from src.indexer.document_processor import process_directory
from src.indexer.indexer import run_indexing_pipeline

console = Console()


def dry_run(kb_path: Path) -> None:
    """Count documents and chunks without embedding or uploading anything."""
    console.print(f"[bold]Dry run — scanning: {kb_path.resolve()}[/bold]")

    total_files = 0
    total_chunks = 0
    file_summary = []

    for root, _, files in __import__("os").walk(kb_path):
        for filename in sorted(files):
            path = Path(root) / filename
            if path.suffix.lower() not in (".pdf", ".docx", ".doc"):
                continue

            chunks = list(
                process_directory(
                    Path(root),
                    chunk_size=settings.chunk_size_tokens,
                    overlap_ratio=settings.chunk_overlap_ratio,
                )
            )
            # process_directory yields all files under root; filter to current file
            # For simplicity in dry-run, use the direct process_document call
            from src.indexer.document_processor import process_document
            file_chunks = process_document(
                path,
                chunk_size=settings.chunk_size_tokens,
                overlap_ratio=settings.chunk_overlap_ratio,
            )
            total_files += 1
            total_chunks += len(file_chunks)
            file_summary.append((path.name, len(file_chunks)))

    console.print(f"\nFound [bold]{total_files}[/bold] documents → [bold]{total_chunks}[/bold] chunks\n")
    for name, count in file_summary:
        console.print(f"  {name:<60} {count:>4} chunks")

    console.print(
        f"\nAt batch size {100}, this would require "
        f"~{(total_chunks // 100) + 1} embedding API call(s) and "
        f"~{(total_chunks // 100) + 1} upload batch(es)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index governance documents into Azure AI Search."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to knowledge base directory (default: value from .env / settings)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and count documents without uploading",
    )
    args = parser.parse_args()

    kb_path = Path(args.path or settings.knowledge_base_path)

    if not kb_path.exists():
        console.print(
            f"[red]Knowledge base path not found: {kb_path.resolve()}[/red]\n"
            "Run [bold]python scripts/setup_infrastructure.py[/bold] first, "
            "then add documents to the knowledge-base/ directory."
        )
        sys.exit(1)

    if args.dry_run:
        dry_run(kb_path)
        return

    run_indexing_pipeline(knowledge_base_path=str(kb_path))


if __name__ == "__main__":
    main()
