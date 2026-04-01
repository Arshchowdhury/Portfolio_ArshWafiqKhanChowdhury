"""
Document indexing pipeline — process, embed, upload.

Embedding batch size is set to 100 (well below the Azure Search 1000-doc limit)
to keep memory footprint reasonable when running against large governance corpora.
The OpenAI embedding API batch size is separate and handled inside generate_embeddings.

Run via scripts/run_indexer.py rather than importing directly.
"""

import time
from pathlib import Path
from typing import Iterator

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from config.settings import settings
from src.indexer.document_processor import DocumentChunk, process_directory
from src.indexer.search_index import create_or_update_index

console = Console()

BATCH_SIZE = 100


def get_search_client() -> SearchClient:
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=AzureKeyCredential(settings.azure_search_key),
    )


def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
    )


def generate_embeddings(texts: list[str], client: AzureOpenAI) -> list[list[float]]:
    """Generate embeddings for a list of texts using text-embedding-ada-002."""
    try:
        response = client.embeddings.create(
            model=settings.azure_openai_embedding_deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        if "429" in str(e):
            # Single retry after 60s — the Azure OpenAI rate limit window resets
            # within a minute for the TPM quota. For production workloads with
            # large corpora, replace this with tenacity or a proper backoff library.
            console.print("[yellow]Rate limited. Waiting 60s...[/yellow]")
            time.sleep(60)
            response = client.embeddings.create(
                model=settings.azure_openai_embedding_deployment,
                input=texts,
            )
            return [item.embedding for item in response.data]
        raise


def chunks_to_documents(chunks: list[DocumentChunk]) -> list[dict]:
    """Convert DocumentChunk dataclasses to the dict format expected by the Search SDK."""
    return [
        {
            "id": chunk.id,
            "title": chunk.title,
            "content": chunk.content,
            "sourceUrl": chunk.source_url,
            "author": chunk.author,
            "lastModified": chunk.last_modified or None,
            "chunkIndex": chunk.chunk_index,
            "totalChunks": chunk.total_chunks,
            "contentVector": chunk.content_vector,
        }
        for chunk in chunks
    ]


def _batched(items: list, size: int) -> Iterator[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def run_indexing_pipeline(knowledge_base_path: str = None) -> None:
    """
    Full indexing pipeline: ensure index exists, process documents,
    generate embeddings, upload to Azure AI Search.
    """
    kb_path = Path(knowledge_base_path or settings.knowledge_base_path)

    if not kb_path.exists():
        console.print(f"[red]Knowledge base path not found: {kb_path}[/red]")
        return

    console.print("[bold]Starting indexing pipeline[/bold]")
    console.print(f"Knowledge base: {kb_path.resolve()}")

    # Step 1: Ensure index exists
    console.print("\n[cyan]Step 1: Ensuring search index exists...[/cyan]")
    create_or_update_index()

    # Step 2: Process documents
    console.print("\n[cyan]Step 2: Processing documents...[/cyan]")
    all_chunks: list[DocumentChunk] = list(
        process_directory(
            kb_path,
            chunk_size=settings.chunk_size_tokens,
            overlap_ratio=settings.chunk_overlap_ratio,
        )
    )

    if not all_chunks:
        console.print("[yellow]No documents found to index.[/yellow]")
        return

    console.print(f"Processed {len(all_chunks)} chunks from {kb_path}")

    # Step 3: Generate embeddings
    console.print("\n[cyan]Step 3: Generating embeddings...[/cyan]")
    openai_client = get_openai_client()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} chunks"),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding...", total=len(all_chunks))

        for batch in _batched(all_chunks, BATCH_SIZE):
            texts = [chunk.content for chunk in batch]
            embeddings = generate_embeddings(texts, openai_client)
            for chunk, embedding in zip(batch, embeddings):
                chunk.content_vector = embedding
            progress.advance(task, len(batch))

    # Step 4: Upload to Azure AI Search
    console.print("\n[cyan]Step 4: Uploading to Azure AI Search...[/cyan]")
    search_client = get_search_client()

    total_uploaded = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} chunks"),
        console=console,
    ) as progress:
        task = progress.add_task("Uploading...", total=len(all_chunks))

        for batch in _batched(all_chunks, BATCH_SIZE):
            documents = chunks_to_documents(batch)
            result = search_client.upload_documents(documents=documents)
            succeeded = sum(1 for r in result if r.succeeded)
            total_uploaded += succeeded
            progress.advance(task, len(batch))

    console.print(
        f"\n[green]Indexing complete. {total_uploaded}/{len(all_chunks)} chunks uploaded.[/green]"
    )
