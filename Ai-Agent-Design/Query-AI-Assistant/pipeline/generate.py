"""
generate.py — Apex Query Assistant
RAG generation: retrieval context + GPT-4o → grounded response.

Ties together the retrieval and generation layers.
Loads the grounding prompt from the versioned prompt file,
injects retrieved context, and calls GPT-4o to generate
a citation-grounded response.

Author: Arsh Wafiq Khan Chowdhury
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Config
from retrieve import RetrievalEngine, RetrievalResult

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class GenerationResponse:
    """The full response from the RAG pipeline."""
    answer: str                           # The generated response
    sources: list[str]                    # Source documents cited
    retrieved_chunks: list[RetrievalResult]  # Raw chunks used
    query: str                            # Original query
    escalation_required: bool = False     # True if the query should be escalated
    escalation_reason: str = ""           # Why escalation was triggered
    confidence: str = "high"             # "high" | "medium" | "low"


class RAGPipeline:
    """
    Full RAG pipeline: query → retrieve → generate → respond.

    Usage:
        pipeline = RAGPipeline(config)
        response = pipeline.query("What is the late payment penalty?")
        print(response.answer)
    """

    # Topics that always trigger escalation — no generative response
    ESCALATION_TOPICS = [
        r"\baccount\s*(number|detail|balance|statement)\b",
        r"\bpolicy\s*number\b",
        r"\bpassword\b",
        r"\bcomplaint\b",
        r"\bspeak\s*to\s*(a\s*)?(human|person|agent|someone)\b",
        r"\blegal\s*advice\b",
        r"\bfinancial\s*advice\b",
        r"\bsue\b|\blawsuit\b|\blitigation\b",
    ]

    def __init__(self, config: Config):
        self.config = config
        self.retrieval = RetrievalEngine(config)
        self.openai_client = AzureOpenAI(
            azure_endpoint=config.openai_endpoint,
            azure_ad_token_provider=self._get_token,
            api_version=config.openai_api_version,
        )
        self.system_prompt = self._load_system_prompt()
        self.grounding_prompt_template = self._load_grounding_prompt()

    def _get_token(self) -> str:
        from azure.identity import DefaultAzureCredential
        return DefaultAzureCredential().get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token

    def query(
        self,
        user_query: str,
        audience: str = "customer",
        category_filter: str = None,
    ) -> GenerationResponse:
        """
        Process a user query through the full RAG pipeline.

        Steps:
          1. Check for escalation triggers
          2. Retrieve relevant document chunks
          3. Build grounding prompt with context
          4. Generate response via GPT-4o
          5. Parse and return structured response
        """

        # Step 1: Escalation check
        escalation_reason = self._check_escalation(user_query)
        if escalation_reason:
            return GenerationResponse(
                answer=(
                    "I need to pass this to our support team who can help you directly. "
                    "I'm connecting you now."
                ),
                sources=[],
                retrieved_chunks=[],
                query=user_query,
                escalation_required=True,
                escalation_reason=escalation_reason,
                confidence="high",
            )

        # Step 2: Retrieve
        chunks = self.retrieval.retrieve(
            query=user_query,
            audience=audience,
            category_filter=category_filter,
        )

        # Step 3: Build grounding prompt
        context = self.retrieval.format_context(chunks)
        grounding_prompt = self.grounding_prompt_template.format(
            retrieved_chunks=context,
            user_query=user_query,
        )

        # Step 4: Generate
        raw_answer = self._generate(grounding_prompt)

        # Step 5: Parse response
        sources = self._extract_sources(raw_answer)
        confidence = self._assess_confidence(chunks, raw_answer)

        return GenerationResponse(
            answer=raw_answer,
            sources=sources,
            retrieved_chunks=chunks,
            query=user_query,
            escalation_required=False,
            confidence=confidence,
        )

    def _check_escalation(self, query: str) -> str:
        """
        Check if query matches escalation topics.
        Returns the reason string if escalation needed, else empty string.
        """
        query_lower = query.lower()
        for pattern in self.ESCALATION_TOPICS:
            if re.search(pattern, query_lower):
                return f"Query matched escalation pattern: {pattern}"
        return ""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate(self, grounding_prompt: str) -> str:
        """Call GPT-4o with system prompt and grounding prompt."""
        response = self.openai_client.chat.completions.create(
            model=self.config.openai_deployment,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": grounding_prompt},
            ],
            temperature=0.1,         # Low temperature: factual, consistent responses
            max_tokens=400,          # Caps response at ~200 words
            top_p=0.95,
        )
        return response.choices[0].message.content.strip()

    def _extract_sources(self, answer: str) -> list[str]:
        """Extract cited source documents from the answer text."""
        # Matches patterns like "Source: PolicyDocument.pdf, Section 4.1"
        sources = re.findall(r"Source:\s*([^\n,]+)", answer)
        return [s.strip() for s in sources]

    def _assess_confidence(
        self, chunks: list[RetrievalResult], answer: str
    ) -> str:
        """
        Assess response confidence based on retrieval quality.

        High:   3+ chunks with reranker_score > 2.0
        Medium: 1–2 chunks retrieved or lower scores
        Low:    No chunks retrieved or refusal response detected
        """
        if not chunks:
            return "low"

        refusal_phrases = [
            "don't have confident information",
            "cannot find",
            "not covered in",
        ]
        if any(phrase in answer.lower() for phrase in refusal_phrases):
            return "low"

        high_quality = [c for c in chunks if c.reranker_score > 2.0]
        if len(high_quality) >= 3:
            return "high"
        if len(chunks) >= 1:
            return "medium"
        return "low"

    def _load_system_prompt(self) -> str:
        """Load the versioned system prompt from the prompts directory."""
        prompt_path = PROMPTS_DIR / "system-prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"System prompt not found at {prompt_path}. "
                "Ensure prompts/system-prompt.md exists."
            )
        content = prompt_path.read_text(encoding="utf-8")
        # Extract only the prompt block (between ```...```)
        match = re.search(r"```\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content

    def _load_grounding_prompt(self) -> str:
        """Load the versioned grounding prompt template."""
        prompt_path = PROMPTS_DIR / "grounding-prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Grounding prompt not found at {prompt_path}."
            )
        content = prompt_path.read_text(encoding="utf-8")
        match = re.search(r"```\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return content


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from config import load_config

    logging.basicConfig(level=logging.INFO)
    config = load_config()
    pipeline = RAGPipeline(config)

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the late payment policy?"
    response = pipeline.query(query)

    print(f"\nQuery: {response.query}")
    print(f"Confidence: {response.confidence}")
    print(f"Escalation required: {response.escalation_required}")
    if response.escalation_required:
        print(f"Reason: {response.escalation_reason}")
    print(f"\nAnswer:\n{response.answer}")
    print(f"\nSources: {', '.join(response.sources) or 'None cited'}")
