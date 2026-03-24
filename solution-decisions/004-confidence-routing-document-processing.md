# ADR 004 — Confidence-Based Routing for AI Document Processing

**Status:** Accepted
**Date:** March 2026
**Context:** Automated Document Processing workflow automation project

---

## Context

The document processing automation project used Azure OpenAI to classify and extract data from incoming documents. A design decision was required on how to handle cases where the AI model's output could not be trusted with sufficient certainty — whether to process all documents automatically, reject uncertain documents, or route them differently based on model confidence.

---

## Decision

Implement confidence-based routing: documents above a defined confidence threshold are processed automatically; documents below the threshold are routed to a human review queue with the AI's draft output pre-populated.

---

## Options Considered

**Option 1: Full automation (process all documents automatically)**
- Pros: Maximum efficiency; lowest human effort
- Cons: AI classification errors propagate silently; unsuitable where downstream errors have operational or compliance consequences; erodes user trust when errors surface

**Option 2: Human review for all documents**
- Pros: Zero automation risk; full human oversight
- Cons: Eliminates the value of automation; does not address the original problem (volume and time)

**Option 3: Confidence-based routing (chosen)**
- Pros: High-confidence documents processed at speed with no manual intervention; low-confidence documents caught before errors propagate; human reviewers work on the hard cases, not the routine ones; AI draft output pre-populated in the review queue reduces reviewer effort on uncertain cases
- Cons: Requires calibration of the confidence threshold; threshold tuning is ongoing work; adds architectural complexity compared to simple automation

---

## Rationale

The document processing context involved records where classification errors had downstream operational consequences. Full automation without a confidence gate would create a silent failure mode — errors would only be discovered after they had propagated into downstream systems.

Confidence-based routing aligns with a broader design principle applied across the AI projects in this portfolio: automation should reduce the queue, not eliminate judgment. The human reviewer's role is not replaced by the AI; it is redefined. The AI handles volume; the human handles ambiguity.

The confidence threshold was set conservatively at first (0.85) and adjusted based on error rate monitoring. Pre-populating the review queue with the AI's draft output meant reviewers were correcting rather than starting from scratch — reducing review time without removing oversight.

---

## Consequences

- Automation handles approximately 70–80% of document volume above the confidence threshold
- Human review queue is scoped to genuinely ambiguous cases, not random sampling
- Threshold calibration is a defined operational responsibility, not a one-time setup
- This pattern is applicable across AI-augmented workflows wherever output errors carry downstream risk

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant*
