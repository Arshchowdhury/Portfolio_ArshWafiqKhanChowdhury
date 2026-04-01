"""
Unit tests for the RAG query engine.

All Azure OpenAI and Azure AI Search calls are mocked so tests run
fully offline without requiring any cloud credentials.

Run with:
    pytest tests/test_search.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# Add project root so imports resolve without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.search.query_engine import (
    QueryEngine,
    QueryResult,
    Citation,
    _confidence_band,
    _build_context,
)


# ---------------------------------------------------------------------------
# _confidence_band
# ---------------------------------------------------------------------------

class TestConfidenceBand:
    def test_high_at_exactly_0_85(self):
        assert _confidence_band(0.85) == "High"

    def test_high_above_0_85(self):
        assert _confidence_band(1.5) == "High"
        assert _confidence_band(4.0) == "High"

    def test_medium_at_exactly_0_70(self):
        assert _confidence_band(0.70) == "Medium"

    def test_medium_between_0_70_and_0_85(self):
        assert _confidence_band(0.77) == "Medium"
        assert _confidence_band(0.84) == "Medium"

    def test_escalated_below_0_70(self):
        assert _confidence_band(0.69) == "Escalated"
        assert _confidence_band(0.0) == "Escalated"

    def test_boundary_just_below_high(self):
        assert _confidence_band(0.849) == "Medium"

    def test_boundary_just_below_medium(self):
        assert _confidence_band(0.699) == "Escalated"


# ---------------------------------------------------------------------------
# _build_context
# ---------------------------------------------------------------------------

class TestBuildContext:
    def _make_result(self, title, content, source_url="", chunk_index=0):
        return {
            "title": title,
            "content": content,
            "sourceUrl": source_url,
            "chunkIndex": chunk_index,
        }

    def test_single_result_formats_correctly(self):
        results = [self._make_result("EU AI Act", "Article 5 prohibits...", "eu_ai_act.pdf", 2)]
        context, citations = _build_context(results)

        assert "[Document 1: EU AI Act (chunk 2)]" in context
        assert "Article 5 prohibits..." in context
        assert len(citations) == 1
        assert citations[0].title == "EU AI Act"
        assert citations[0].chunk_index == 2

    def test_multiple_results_separated_by_divider(self):
        results = [
            self._make_result("Doc A", "Content A"),
            self._make_result("Doc B", "Content B"),
        ]
        context, citations = _build_context(results)

        assert "---" in context
        assert "[Document 1: Doc A" in context
        assert "[Document 2: Doc B" in context
        assert len(citations) == 2

    def test_missing_fields_use_defaults(self):
        results = [{}]  # All fields missing
        context, citations = _build_context(results)

        assert "Unknown" in context
        assert citations[0].title == "Unknown"
        assert citations[0].source_url == ""
        assert citations[0].chunk_index == 0

    def test_empty_results_produces_empty_context(self):
        context, citations = _build_context([])
        assert context == ""
        assert citations == []


# ---------------------------------------------------------------------------
# QueryEngine (mocked Azure clients)
# ---------------------------------------------------------------------------

def _make_mock_engine():
    """Return a QueryEngine with both Azure clients mocked out."""
    with patch("src.search.query_engine.SearchClient"), \
         patch("src.search.query_engine.AzureOpenAI"):
        engine = QueryEngine()

    engine._search_client = MagicMock()
    engine._openai_client = MagicMock()
    return engine


def _mock_embedding_response(vector: list[float]):
    """Helper to build a mock embeddings.create() response."""
    mock_data = MagicMock()
    mock_data.embedding = vector
    return MagicMock(data=[mock_data])


def _mock_search_result(title: str, content: str, score: float, chunk_index: int = 0):
    """Helper to build a mock Azure Search result dict."""
    return {
        "id": f"id-{chunk_index}",
        "title": title,
        "content": content,
        "sourceUrl": f"{title.lower().replace(' ', '_')}.pdf",
        "chunkIndex": chunk_index,
        "totalChunks": 5,
        "@search.reranker_score": score,
    }


class TestQueryEngineEmbedQuery:
    def test_calls_embeddings_create_with_correct_model(self):
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )

        from config.settings import settings
        vector = engine._embed_query("What is the EU AI Act?")

        engine._openai_client.embeddings.create.assert_called_once()
        call_kwargs = engine._openai_client.embeddings.create.call_args.kwargs
        assert call_kwargs["model"] == settings.azure_openai_embedding_deployment
        assert call_kwargs["input"] == "What is the EU AI Act?"
        assert vector == [0.1] * 1536


class TestQueryEngineHybridSearch:
    def test_filters_results_below_threshold(self):
        engine = _make_mock_engine()

        raw_results = [
            _mock_search_result("EU AI Act", "High-risk systems...", score=0.91),
            _mock_search_result("NIST RMF", "Govern function...", score=0.72),
            _mock_search_result("Old Doc", "Outdated info...", score=0.55),  # below 0.7
        ]
        engine._search_client.search.return_value = iter(raw_results)

        qualified = engine._hybrid_search("What is a high-risk AI system?", [0.1] * 1536)

        assert len(qualified) == 2
        scores = [r["_reranker_score"] for r in qualified]
        assert all(s >= 0.7 for s in scores)
        assert 0.55 not in scores

    def test_returns_empty_when_all_below_threshold(self):
        engine = _make_mock_engine()
        raw_results = [
            _mock_search_result("Irrelevant", "Nothing useful.", score=0.3),
        ]
        engine._search_client.search.return_value = iter(raw_results)

        result = engine._hybrid_search("Very obscure question", [0.0] * 1536)
        assert result == []

    def test_passes_correct_search_parameters(self):
        engine = _make_mock_engine()
        engine._search_client.search.return_value = iter([])

        engine._hybrid_search("test query", [0.5] * 1536)

        call_kwargs = engine._search_client.search.call_args.kwargs
        assert call_kwargs["search_text"] == "test query"
        assert "vector_queries" in call_kwargs
        # Semantic query type
        from azure.search.documents.models import QueryType
        assert call_kwargs["query_type"] == QueryType.SEMANTIC


class TestQueryEngineFullQuery:
    def test_escalates_when_no_qualifying_results(self):
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )
        engine._search_client.search.return_value = iter([])  # No results

        result = engine.query("Completely unknown topic", session_id="session-001")

        assert isinstance(result, QueryResult)
        assert result.escalated is True
        assert result.confidence_band == "Escalated"
        assert result.top_score == 0.0
        assert result.citations == []
        assert "escalated" in result.response.lower()

    def test_returns_response_when_results_qualify(self):
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )

        raw_results = [_mock_search_result("EU AI Act", "Article 5...", score=0.92)]
        engine._search_client.search.return_value = iter(raw_results)

        mock_choice = MagicMock()
        mock_choice.message.content = "Article 5 of the EU AI Act prohibits... [Source: EU AI Act]"
        engine._openai_client.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        result = engine.query("What does Article 5 prohibit?", session_id="session-002")

        assert result.escalated is False
        assert result.confidence_band == "High"
        assert result.top_score == 0.92
        assert len(result.citations) == 1
        assert result.citations[0].title == "EU AI Act"
        assert "Article 5" in result.response

    def test_medium_confidence_band_assigned_correctly(self):
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )

        raw_results = [_mock_search_result("NIST RMF", "Govern...", score=0.75)]
        engine._search_client.search.return_value = iter(raw_results)

        mock_choice = MagicMock()
        mock_choice.message.content = "The NIST RMF Govern function..."
        engine._openai_client.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        result = engine.query("Summarise the NIST AI RMF", session_id="session-003")

        assert result.confidence_band == "Medium"
        assert result.escalated is False

    def test_session_id_propagated_to_result(self):
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )
        engine._search_client.search.return_value = iter([])

        result = engine.query("Any question", session_id="my-session-xyz")
        assert result.session_id == "my-session-xyz"

    def test_low_temperature_used_for_generation(self):
        """GPT-4o must be called with temperature=0.1 for factual grounding."""
        engine = _make_mock_engine()
        engine._openai_client.embeddings.create.return_value = _mock_embedding_response(
            [0.1] * 1536
        )

        raw_results = [_mock_search_result("Policy Doc", "Policy content.", score=0.88)]
        engine._search_client.search.return_value = iter(raw_results)

        mock_choice = MagicMock()
        mock_choice.message.content = "Policy response."
        engine._openai_client.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        engine.query("Question about policy")

        create_call = engine._openai_client.chat.completions.create.call_args.kwargs
        assert create_call["temperature"] == 0.1


# ---------------------------------------------------------------------------
# Citation dataclass
# ---------------------------------------------------------------------------

class TestCitation:
    def test_citation_fields(self):
        c = Citation(title="EU AI Act", source_url="public/eu.pdf", chunk_index=3)
        assert c.title == "EU AI Act"
        assert c.source_url == "public/eu.pdf"
        assert c.chunk_index == 3
