# ADR 005 — Groq API over OpenAI for BA Process Documentation Tool

**Status:** Accepted
**Date:** March 2026
**Context:** BA Process Documentation Generator — public web tool

---

## Context

The BA Process Documentation Generator is a public-facing web tool that calls an LLM API to generate consulting artifacts (SIPOC, discovery questions, pain points, frameworks) from a process description. A decision was required on which LLM provider to use as the default.

---

## Decision

Use Groq (llama-3.3-70b-versatile) as the default API, with OpenAI as a documented alternative.

---

## Options Considered

**Option 1: OpenAI (GPT-4o or GPT-3.5-turbo)**
- Pros: Highest output quality; widely understood; JSON response format support; strong instruction-following
- Cons: Paid API with no free tier; cost per request adds up for a public tool; requires users to have a billing-enabled OpenAI account

**Option 2: Groq (llama-3.3-70b) — chosen**
- Pros: Free tier with generous rate limits; extremely fast inference (typically <2s); supports JSON response format; llama-3.3-70b produces high-quality structured output suitable for this task; API key signup takes 30 seconds
- Cons: Not as well-known as OpenAI; dependent on Groq's infrastructure; model quality slightly below GPT-4o for complex reasoning tasks

**Option 3: Local/self-hosted model (Ollama)**
- Pros: No API key required; fully private; no cost
- Cons: Requires user to run a local model server; not practical for a public web tool; incompatible with browser-based deployment

---

## Rationale

The primary audience for this tool includes BAs, consultants, and students who may not have an OpenAI billing account. A free API with no credit card requirement removes a significant friction point for adoption.

For the specific task — generating structured SIPOC tables, discovery questions, and framework recommendations — llama-3.3-70b-versatile produces output of sufficient quality. This is not a task requiring the frontier reasoning of GPT-4o; it is a structured document generation task with a well-defined JSON schema.

The combination of free access, fast inference, and JSON response format support made Groq the practical choice for a tool intended to be publicly shared.

---

## Consequences

- Tool is accessible without a paid API subscription; lowers adoption friction
- Users who prefer OpenAI can substitute their API key (documented in the tool)
- API key is used client-side only, never stored on a server
- Response times consistently under 3 seconds for typical inputs

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant*
