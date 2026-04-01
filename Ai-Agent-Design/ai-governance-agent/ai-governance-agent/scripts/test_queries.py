"""
End-to-end query test harness.

Runs a set of representative governance queries through the full RAG pipeline
and prints the results in a structured format.  Use this script to:

  1. Validate the pipeline is working after indexing
  2. Regression-test changes to chunking strategy or confidence threshold
  3. Demonstrate the system's capabilities during a portfolio review

Each test query covers a distinct area of AI governance so the output
demonstrates breadth of knowledge coverage.

Usage:
    python scripts/test_queries.py

    # Run a single query interactively
    python scripts/test_queries.py --query "What does the EU AI Act say about prohibited uses?"

    # Export results to JSON for further analysis
    python scripts/test_queries.py --output results.json
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

# Add project root to sys.path so config and src imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.search.query_engine import QueryEngine, QueryResult

console = Console()

# ---------------------------------------------------------------------------
# Sample queries — each targets a distinct governance domain
# ---------------------------------------------------------------------------

TEST_QUERIES = [
    # EU AI Act
    "What are the prohibited AI practices under the EU AI Act?",
    "How does the EU AI Act define 'high-risk' AI systems and what obligations apply?",
    "What conformity assessment procedures are required for high-risk AI systems?",

    # NIST AI RMF
    "Summarise the four core functions of the NIST AI Risk Management Framework.",
    "How does the NIST AI RMF address AI transparency and explainability?",

    # Internal policy scenarios
    "What are our internal requirements for AI model documentation before deployment?",
    "How should employees escalate concerns about AI-generated outputs they believe are incorrect?",

    # Risk management
    "What controls does our AI governance policy require for generative AI use cases?",
    "Describe the AI incident response process and who is responsible for leading it.",

    # Cross-framework
    (
        "How do the EU AI Act requirements for human oversight compare with our internal "
        "AI governance policy?"
    ),
]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

BAND_COLOURS = {
    "High": "green",
    "Medium": "yellow",
    "Escalated": "red",
}


def _band_styled(band: str) -> str:
    colour = BAND_COLOURS.get(band, "white")
    return f"[{colour}]{band}[/{colour}]"


def print_result(index: int, result: QueryResult) -> None:
    band_str = _band_styled(result.confidence_band)
    score_str = f"{result.top_score:.3f}"

    header = (
        f"[bold]Query {index}[/bold]  |  "
        f"Confidence: {band_str}  |  "
        f"Score: {score_str}  |  "
        f"Escalated: {'yes' if result.escalated else 'no'}"
    )

    body = f"[bold dim]Q:[/bold dim] {result.query}\n\n"

    if result.escalated:
        body += f"[red]{result.response}[/red]"
    else:
        body += result.response

        if result.citations:
            body += "\n\n[bold dim]Citations:[/bold dim]"
            for c in result.citations:
                body += f"\n  • {c.title} (chunk {c.chunk_index})"
                if c.source_url:
                    body += f"  —  {c.source_url}"

    console.print(Panel(body, title=header, expand=False))


def print_summary(results: list[QueryResult]) -> None:
    table = Table(title="Test Summary", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Query (truncated)", min_width=40)
    table.add_column("Band", min_width=10)
    table.add_column("Score", min_width=7)
    table.add_column("Citations")

    for i, r in enumerate(results, 1):
        band_str = _band_styled(r.confidence_band)
        citation_count = str(len(r.citations)) if not r.escalated else "—"
        table.add_row(
            str(i),
            r.query[:60] + ("..." if len(r.query) > 60 else ""),
            band_str,
            f"{r.top_score:.3f}",
            citation_count,
        )

    console.print("\n")
    console.print(table)

    high = sum(1 for r in results if r.confidence_band == "High")
    medium = sum(1 for r in results if r.confidence_band == "Medium")
    escalated = sum(1 for r in results if r.escalated)

    console.print(
        f"\n[green]High[/green]: {high}  "
        f"[yellow]Medium[/yellow]: {medium}  "
        f"[red]Escalated[/red]: {escalated}  "
        f"out of {len(results)} queries\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run test queries against the governance agent.")
    parser.add_argument("--query", type=str, help="Run a single custom query")
    parser.add_argument("--output", type=str, help="Save results to a JSON file")
    args = parser.parse_args()

    engine = QueryEngine()
    session_id = str(uuid.uuid4())

    queries = [args.query] if args.query else TEST_QUERIES
    results: list[QueryResult] = []

    console.print(
        f"\n[bold]AI Governance Agent — Query Test Harness[/bold]\n"
        f"Session: {session_id}\n"
        f"Queries: {len(queries)}\n"
    )
    console.rule()

    for i, query in enumerate(queries, 1):
        console.print(f"\n[dim]Running query {i}/{len(queries)}...[/dim]")
        try:
            result = engine.query(query, session_id=session_id)
            results.append(result)
            print_result(i, result)
        except Exception as exc:
            console.print(f"[red]Query {i} failed: {exc}[/red]")

    console.rule()
    print_summary(results)

    if args.output:
        output_path = Path(args.output)
        serialisable = [
            {
                "query": r.query,
                "response": r.response,
                "confidence_band": r.confidence_band,
                "top_score": r.top_score,
                "escalated": r.escalated,
                "citations": [
                    {
                        "title": c.title,
                        "source_url": c.source_url,
                        "chunk_index": c.chunk_index,
                    }
                    for c in r.citations
                ],
            }
            for r in results
        ]
        output_path.write_text(json.dumps(serialisable, indent=2, ensure_ascii=False))
        console.print(f"[green]Results saved to {output_path}[/green]")


if __name__ == "__main__":
    main()
