"""
One-time Azure infrastructure setup script.

Run this ONCE before indexing any documents.  It:
1. Validates that all required environment variables are present
2. Creates or updates the Azure AI Search index (schema + vector + semantic config)
3. Verifies the index is reachable and returns its field count
4. Creates the local audit log directory

Pre-requisites:
  - Azure AI Search resource provisioned (Basic tier minimum for semantic ranker)
  - Azure OpenAI resource with:
      * gpt-4o deployment named "gpt-4o"
      * text-embedding-ada-002 deployment named "text-embedding-ada-002"
  - .env file populated from .env.example

Usage:
    python scripts/setup_infrastructure.py
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so config and src imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table

from config.settings import settings
from src.indexer.search_index import create_or_update_index, index_exists

console = Console()

# ---------------------------------------------------------------------------
# Environment validation
# ---------------------------------------------------------------------------

REQUIRED_ENV_VARS = [
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY",
]

OPTIONAL_ENV_VARS = [
    "SHAREPOINT_SITE_ID",
    "SHAREPOINT_LIST_ID",
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
]


def validate_env() -> bool:
    """Check that all required environment variables are set."""
    console.print("\n[bold cyan]Checking environment variables...[/bold cyan]")
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Variable")
    table.add_column("Status")

    for var in REQUIRED_ENV_VARS:
        status = "[green]✓ Set[/green]" if os.getenv(var) else "[red]✗ Missing[/red]"
        table.add_row(var, status)

    for var in OPTIONAL_ENV_VARS:
        status = "[green]✓ Set[/green]" if os.getenv(var) else "[yellow]– Not set (optional)[/yellow]"
        table.add_row(var, status)

    console.print(table)

    if missing:
        console.print(
            f"\n[red]Missing required variables: {', '.join(missing)}[/red]"
        )
        console.print(
            "Copy [bold].env.example[/bold] to [bold].env[/bold] and populate the missing values."
        )
        return False

    console.print("\n[green]All required variables present.[/green]")
    return True


def setup_search_index() -> bool:
    """Create or update the Azure AI Search index."""
    console.print("\n[bold cyan]Setting up Azure AI Search index...[/bold cyan]")
    console.print(f"  Endpoint : {settings.azure_search_endpoint}")
    console.print(f"  Index    : {settings.azure_search_index_name}")

    try:
        create_or_update_index()

        if index_exists():
            console.print(
                f"\n[green]✓ Index '{settings.azure_search_index_name}' is ready.[/green]"
            )
            return True
        else:
            console.print("\n[red]Index creation reported success but index not found.[/red]")
            return False

    except Exception as exc:
        console.print(f"\n[red]Index setup failed: {exc}[/red]")
        console.print(
            "Common causes:\n"
            "  - Incorrect AZURE_SEARCH_ENDPOINT format (must include https://)\n"
            "  - Invalid AZURE_SEARCH_KEY\n"
            "  - Azure AI Search resource is on Free tier (semantic ranker requires Basic+)"
        )
        return False


def setup_audit_directory() -> None:
    """Create the local audit log directory if it doesn't exist."""
    audit_path = Path(settings.audit_log_path).parent
    audit_path.mkdir(parents=True, exist_ok=True)
    console.print(f"\n[green]✓ Audit log directory ready: {audit_path.resolve()}[/green]")


def setup_knowledge_base_directory() -> None:
    """Create the knowledge base directory if it doesn't exist."""
    kb_path = Path(settings.knowledge_base_path)
    if not kb_path.exists():
        kb_path.mkdir(parents=True, exist_ok=True)
        console.print(
            f"\n[yellow]Knowledge base directory created: {kb_path.resolve()}\n"
            "Add your governance documents (PDF or DOCX) before running the indexer.[/yellow]"
        )
    else:
        doc_count = sum(
            1 for f in kb_path.rglob("*")
            if f.suffix.lower() in (".pdf", ".docx", ".doc")
        )
        console.print(
            f"\n[green]✓ Knowledge base: {kb_path.resolve()} "
            f"({doc_count} document(s) found)[/green]"
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    console.print("[bold]AI Governance Agent — Infrastructure Setup[/bold]")
    console.rule()

    # 1. Validate environment
    if not validate_env():
        sys.exit(1)

    # 2. Create search index
    if not setup_search_index():
        sys.exit(1)

    # 3. Local directories
    setup_audit_directory()
    setup_knowledge_base_directory()

    console.rule()
    console.print(
        "\n[bold green]Setup complete.[/bold green]\n\n"
        "Next steps:\n"
        "  1. Add governance documents to the [bold]knowledge-base/[/bold] directory\n"
        "     (see knowledge-base/README.md for recommended public documents)\n"
        "  2. Run [bold]python scripts/run_indexer.py[/bold] to index documents\n"
        "  3. Run [bold]python scripts/test_queries.py[/bold] to validate the pipeline\n"
    )


if __name__ == "__main__":
    main()
