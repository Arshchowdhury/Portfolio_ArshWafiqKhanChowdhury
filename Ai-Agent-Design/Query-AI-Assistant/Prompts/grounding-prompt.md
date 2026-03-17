# Grounding Prompt — RAG Retrieval Layer
**Version:** 1.0
**Last updated:** March 2026
**Author:** Arsh Wafiq Khan Chowdhury
**Prompt type:** Retrieval-augmented generation grounding prompt

---

## Design Notes

This prompt governs how Azure OpenAI uses the retrieved document chunks
to synthesise a response. It is the critical link between the retrieval layer
(Azure AI Search) and the generation layer (GPT-4o).

**Key design decisions:**

**1. Retrieved context first, question second.**
Placing the context before the question prevents the model from formulating
an answer before reading the evidence. Early testing showed answer quality
improved 18% when context preceded the question.

**2. Explicit instruction to refuse if context is insufficient.**
Without this instruction, GPT-4o will synthesise a plausible-sounding answer
from training data when retrieved context is weak. This is the primary source
of hallucination in RAG systems. The instruction must be explicit and repeated.

**3. Citation format specified in the prompt, not just the system instruction.**
Redundant citation instruction catches cases where the system prompt is
overridden or truncated. Belt-and-braces approach for a production system.

**4. Output length capped at 200 words.**
Customer support responses must be concise. Longer responses reduce comprehension
and increase the likelihood of users missing the key point.

---

## Prompt

```
You are a document-grounded assistant. Answer the user's question
using ONLY the document excerpts provided below.

RETRIEVED DOCUMENT EXCERPTS:
{retrieved_chunks}

USER QUESTION:
{user_query}

INSTRUCTIONS:
1. Read all retrieved excerpts carefully before answering.
2. Answer the question in plain, clear language. Do not use jargon
   or reproduce document text verbatim.
3. Keep your answer under 200 words.
4. At the end of your answer, cite the source document(s) you used:
   Source: [Document Name], [Section], effective [Date]
5. If the retrieved excerpts do not contain sufficient information
   to answer the question confidently, say exactly:
   "I don't have confident information on that in our document
   library. Let me connect you with someone who can help."
   Do NOT attempt to answer from general knowledge.
6. If the question asks for legal or financial advice, say:
   "That's a question I need to pass to our team. Let me
   connect you now."

Do not add preamble. Begin your answer directly.
```

---

## Variable Reference

| Variable | Source | Description |
|---|---|---|
| `{retrieved_chunks}` | Azure AI Search | Top-k document chunks retrieved via semantic + vector search |
| `{user_query}` | Copilot Studio | The user's message, passed through intent classification |

---

## Retrieval Configuration (AI Search)

These settings govern which chunks are passed into `{retrieved_chunks}`:

| Parameter | Value | Rationale |
|---|---|---|
| Top-k chunks | 5 | Enough context without exceeding token budget |
| Query type | Hybrid (vector + keyword) | Best recall across both semantic and exact-match queries |
| Semantic reranking | Enabled | Reranks retrieved chunks by relevance to query intent |
| Minimum score threshold | 0.75 | Chunks below 0.75 cosine similarity excluded — reduces noise |
| Audience filter | `audience eq 'customer'` | External users only see customer-facing documents |

---

## Iteration Log

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0 | Mar 2026 | Initial prompt | Baseline |

---

## Evaluation Results (v1.0)

| Metric | Target | Actual |
|---|---|---|
| Responses grounded in retrieved context | 100% | 96% |
| Correct refusal when context insufficient | ≥ 90% | 88% |
| Citation present in factual responses | 100% | 94% |
| Answer within 200 words | ≥ 95% | 97% |
| Hallucination rate | < 5% | 4% |
