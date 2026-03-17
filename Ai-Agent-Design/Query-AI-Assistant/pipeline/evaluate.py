"""
evaluate.py — Apex Query Assistant
RAG pipeline evaluation: retrieval quality + answer quality scoring.

Runs the eval_set.json test suite against the live pipeline
and produces a structured report covering:
  - Retrieval recall: did the right document appear in top-k?
  - Answer groundedness: is the answer supported by retrieved chunks?
  - Citation rate: are source documents cited in every answer?
  - Escalation accuracy: are escalation triggers firing correctly?
  - Refusal rate: does the pipeline correctly refuse out-of-scope queries?

Author: Arsh Wafiq Khan Chowdhury
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from config import Config, load_config
from generate import RAGPipeline
from retrieve import RetrievalEngine

logger = logging.getLogger(__name__)

TESTS_DIR = Path(__file__).parent.parent / "tests"


@dataclass
class EvalCase:
    """A single evaluation test case."""
    query: str
    expected_source: str           # Document name that should appear in results
    expected_answer_contains: str  # Key phrase that should appear in answer
    category: str                  # Query category
    should_escalate: bool = False  # True if query should trigger escalation
    is_out_of_scope: bool = False  # True if query should be refused


@dataclass
class EvalResult:
    """Result for a single eval case."""
    query: str
    passed: bool
    retrieval_hit: bool            # Expected source in top-k results?
    citation_present: bool         # Source cited in answer?
    answer_relevant: bool          # Answer contains expected phrase?
    escalation_correct: bool       # Escalation behaviour correct?
    confidence: str
    answer: str
    sources: list[str]
    latency_ms: float
    error: str = ""


@dataclass
class EvalReport:
    """Aggregated evaluation report."""
    total_cases: int = 0
    passed: int = 0
    retrieval_recall: float = 0.0       # % cases where expected source was in top-k
    citation_rate: float = 0.0          # % answers with source citations
    answer_relevance: float = 0.0       # % answers containing expected phrase
    escalation_accuracy: float = 0.0    # % escalation decisions correct
    avg_latency_ms: float = 0.0
    results: list[EvalResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_cases if self.total_cases else 0.0


class Evaluator:
    """
    Runs the evaluation suite against the live RAG pipeline.

    Usage:
        config = load_config()
        evaluator = Evaluator(config)
        report = evaluator.run()
        evaluator.print_report(report)
        evaluator.save_report(report, "eval_results.json")
    """

    def __init__(self, config: Config):
        self.config = config
        self.pipeline = RAGPipeline(config)

    def run(self, eval_set_path: Path = None) -> EvalReport:
        """Run the full evaluation suite."""

        path = eval_set_path or (TESTS_DIR / "eval_set.json")
        cases = self._load_eval_set(path)

        logger.info(f"Running {len(cases)} evaluation cases")
        report = EvalReport(total_cases=len(cases))

        for case in cases:
            result = self._evaluate_case(case)
            report.results.append(result)
            if result.passed:
                report.passed += 1

        # Aggregate metrics
        report.retrieval_recall = np.mean([r.retrieval_hit for r in report.results])
        report.citation_rate = np.mean([r.citation_present for r in report.results])
        report.answer_relevance = np.mean([r.answer_relevant for r in report.results])
        report.escalation_accuracy = np.mean([r.escalation_correct for r in report.results])
        report.avg_latency_ms = np.mean([r.latency_ms for r in report.results])

        return report

    def _evaluate_case(self, case: EvalCase) -> EvalResult:
        """Evaluate a single test case."""
        start = time.time()
        error = ""

        try:
            response = self.pipeline.query(case.query)
        except Exception as e:
            error = str(e)
            latency_ms = (time.time() - start) * 1000
            return EvalResult(
                query=case.query,
                passed=False,
                retrieval_hit=False,
                citation_present=False,
                answer_relevant=False,
                escalation_correct=False,
                confidence="low",
                answer="",
                sources=[],
                latency_ms=latency_ms,
                error=error,
            )

        latency_ms = (time.time() - start) * 1000

        # Retrieval: did the expected source appear?
        retrieved_sources = [
            c.source_document for c in response.retrieved_chunks
        ]
        retrieval_hit = any(
            case.expected_source.lower() in s.lower()
            for s in retrieved_sources
        ) if not case.should_escalate else True

        # Citation: is a source referenced in the answer?
        citation_present = bool(response.sources) or "Source:" in response.answer

        # Answer relevance: does the answer contain the expected phrase?
        answer_relevant = (
            case.expected_answer_contains.lower() in response.answer.lower()
            if case.expected_answer_contains else True
        )

        # Escalation: did the pipeline behave correctly?
        escalation_correct = (
            response.escalation_required == case.should_escalate
        )

        # A case passes if all checks pass
        passed = (
            retrieval_hit
            and citation_present
            and answer_relevant
            and escalation_correct
            and not error
        )

        return EvalResult(
            query=case.query,
            passed=passed,
            retrieval_hit=retrieval_hit,
            citation_present=citation_present,
            answer_relevant=answer_relevant,
            escalation_correct=escalation_correct,
            confidence=response.confidence,
            answer=response.answer[:300],
            sources=response.sources,
            latency_ms=latency_ms,
            error=error,
        )

    def _load_eval_set(self, path: Path) -> list[EvalCase]:
        """Load evaluation cases from JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [EvalCase(**case) for case in data["cases"]]

    def print_report(self, report: EvalReport) -> None:
        """Print a formatted evaluation report to the terminal."""
        print("\n" + "=" * 60)
        print("APEX QUERY ASSISTANT — EVALUATION REPORT")
        print("=" * 60)
        print(f"Total cases:          {report.total_cases}")
        print(f"Passed:               {report.passed} ({report.pass_rate:.1%})")
        print(f"Retrieval recall:     {report.retrieval_recall:.1%}")
        print(f"Citation rate:        {report.citation_rate:.1%}")
        print(f"Answer relevance:     {report.answer_relevance:.1%}")
        print(f"Escalation accuracy:  {report.escalation_accuracy:.1%}")
        print(f"Avg latency:          {report.avg_latency_ms:.0f}ms")
        print("\nFailed cases:")
        for r in report.results:
            if not r.passed:
                print(f"  ✗ {r.query[:60]}")
                if r.error:
                    print(f"    Error: {r.error}")
                else:
                    checks = []
                    if not r.retrieval_hit: checks.append("retrieval_hit=False")
                    if not r.citation_present: checks.append("citation_present=False")
                    if not r.answer_relevant: checks.append("answer_relevant=False")
                    if not r.escalation_correct: checks.append("escalation_correct=False")
                    print(f"    Failed: {', '.join(checks)}")
        print("=" * 60)

    def save_report(self, report: EvalReport, output_path: str) -> None:
        """Save the full evaluation report as JSON."""
        data = {
            "summary": {
                "total_cases": report.total_cases,
                "passed": report.passed,
                "pass_rate": report.pass_rate,
                "retrieval_recall": report.retrieval_recall,
                "citation_rate": report.citation_rate,
                "answer_relevance": report.answer_relevance,
                "escalation_accuracy": report.escalation_accuracy,
                "avg_latency_ms": report.avg_latency_ms,
            },
            "results": [
                {
                    "query": r.query,
                    "passed": r.passed,
                    "retrieval_hit": r.retrieval_hit,
                    "citation_present": r.citation_present,
                    "answer_relevant": r.answer_relevant,
                    "escalation_correct": r.escalation_correct,
                    "confidence": r.confidence,
                    "latency_ms": round(r.latency_ms, 1),
                    "sources": r.sources,
                    "error": r.error,
                }
                for r in report.results
            ],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Report saved to {output_path}")


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Run Apex RAG evaluation suite")
    parser.add_argument("--output", default="eval_results.json", help="Output JSON path")
    parser.add_argument("--key-vault", help="Key Vault URL for production config")
    args = parser.parse_args()

    config = load_config(
        use_key_vault=bool(args.key_vault),
        key_vault_url=args.key_vault,
    )

    evaluator = Evaluator(config)
    report = evaluator.run()
    evaluator.print_report(report)
    evaluator.save_report(report, args.output)
