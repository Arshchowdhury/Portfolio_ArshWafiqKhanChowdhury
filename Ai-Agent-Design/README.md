# AI Agent Design Portfolio
## Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW

> A collection of original AI agent designs demonstrating end-to-end solution architecture across three industries. Each agent is fully documented with business case, architecture, Azure infrastructure as code, prompt engineering, and governance approach.

---

## Agent Portfolio

| # | Agent | Industry | Primary Problem | Key Technologies |
|---|---|---|---|---|
| 01 | AI Query Assistant (Findfield) | Financial Services | Customer policy queries taking 24–48hrs to resolve | RAG · Azure OpenAI · Bicep IaC · Python pipeline |
| 02 | [CareAssist Incident Agent]| Aged Care | Clinical incidents not escalated within compliance timeframes | Copilot Studio · Power Automate · Teams · Azure OpenAI |
| 03 | [RetailIQ Sales Agent] | Retail / eCommerce | Sales team overwhelmed by manual product and pricing queries | RAG · Copilot Studio · Teams · Power Automate · Bicep |

---

## Capability Coverage

| Capability | Agent 01 | Agent 02 | Agent 03 |
|---|---|---|---|
| RAG over internal documents | ✅ | ✅ | ✅ |
| Azure OpenAI (GPT-4o) | ✅ | ✅ | ✅ |
| Copilot Studio agent design | Partial | ✅ | ✅ |
| Microsoft Teams channel | Partial | ✅ | ✅ |
| Power Automate escalation flows | Partial | ✅ | ✅ |
| Azure Bicep IaC | ✅ | ✅ | ✅ |
| Python RAG pipeline | ✅ | — | — |
| Evaluation framework | ✅ | — | — |
| Regulatory / compliance design | — | ✅ | — |
| Prompt engineering (versioned) | ✅ | ✅ | ✅ |

---

## What Each Agent Demonstrates

### 01 — Apex Query Assistant
The most technically deep artefact. A full Python RAG pipeline from document ingestion through to generation and evaluation. Demonstrates Azure SDK fluency, token-aware chunking, hybrid vector search, confidence routing, and production-grade thinking including the explicit gap between prototype and production.

### 02 — CareAssist Incident Agent
The most compliance-heavy artefact. Demonstrates understanding of regulated industry constraints, human-in-the-loop escalation design, audit trail requirements, and the ability to translate regulatory obligations into technical architecture. Directly relevant to aged care, healthcare, and government technology roles.

### 03 — RetailIQ Sales Agent
The most business-outcome focused artefact. Demonstrates rapid ROI framing, integration with commercial systems (product catalogue, pricing), and multi-channel agent deployment across Teams and web. Relevant to retail, FMCG, and eCommerce technology engagements.

---

## Design Principles Applied Across All Agents

**Business problem first.** Every agent begins with a clearly framed business problem and a design question. Technology choices are made in service of that problem, not the other way around.

**Human-in-the-loop by default.** All three agents include explicit escalation paths to human review. Automation that fails silently destroys trust. Automation that flags uncertainty builds it.

**Governance is not an afterthought.** Each agent documents data sovereignty, access control, audit requirements, and PII handling as first-class design concerns.

**Production thinking.** Every agent includes a "What I Would Do Differently in Production" section that documents the honest gap between prototype and enterprise deployment.

---

## Infrastructure Pattern

All three agents share the same Azure infrastructure pattern, deployed via modular Bicep:

```
Azure OpenAI (GPT-4o)
    ↕ Managed Identity
Azure AI Search (semantic + vector)
    ↕
Azure Blob Storage (document ingestion)
    ↕
Azure Key Vault (no hardcoded credentials)
```

Each agent's `infrastructure/` folder contains a complete, deployable Bicep template scoped to that agent's specific resource configuration.

---

*Prepared by Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW*
*[linkedin.com/in/arsh-wafiq-khan-chowdhury](https://linkedin.com/in/arsh-wafiq-khan-chowdhury) · [github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury](https://github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury)*
*Portfolio artefacts — methodology demonstration only. All client details fictionalised.*

