# AI Agent Design Portfolio

## Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW

> A collection of original AI agent designs demonstrating end-to-end solution architecture across four industries. Each agent is fully documented with business case, architecture, Azure infrastructure as code, prompt engineering, and governance approach.

---

## Agent Portfolio

| # | Agent | Industry | Primary Problem | Key Technologies |
|---|---|---|---|---|
| 01 | Query AI Assistant (Findfield) | Financial Services | Customer policy queries taking 24–48hrs to resolve | RAG · Azure OpenAI · Bicep IaC · Python pipeline |
| 02 | CareAssist Incident Agent | Aged Care | Clinical incidents not escalated within compliance timeframes | Copilot Studio · Power Automate · Teams · Azure OpenAI |
| 03 | RetailIQ Sales Agent | Retail / eCommerce | Sales team overwhelmed by manual product and pricing queries | RAG · Copilot Studio · Teams · Power Automate · Bicep |
| 04 | [AI Governance Advisory Agent](ai-governance-agent/) | Professional Services | AI governance questions bottlenecked through a small specialist team, no audit trail | Copilot Studio · Azure AI Search · Azure OpenAI · Power Automate · Python RAG |

---

## Capability Coverage

| Capability | Agent 01 | Agent 02 | Agent 03 | Agent 04 |
|---|---|---|---|---|
| RAG over internal documents | ✅ | ✅ | ✅ | ✅ |
| Azure OpenAI (GPT-4o) | ✅ | ✅ | ✅ | ✅ |
| Copilot Studio agent design | Partial | ✅ | ✅ | ✅ |
| Microsoft Teams channel | Partial | ✅ | ✅ | ✅ |
| Power Automate escalation flows | Partial | ✅ | ✅ | ✅ |
| Azure Bicep IaC | ✅ | ✅ | ✅ | — |
| Python RAG pipeline | ✅ | — | — | ✅ |
| Unit test suite | — | — | — | ✅ |
| Audit logging (JSONL + SharePoint Graph API) | — | — | — | ✅ |
| Regulatory / compliance design | — | ✅ | — | ✅ |
| Full delivery documentation (SDD, ADR, UAT, Runbook) | — | — | — | ✅ |
| Prompt engineering (versioned) | ✅ | ✅ | ✅ | ✅ |

---

## What Each Agent Demonstrates

### 01 — Query AI Assistant

The most technically deep artefact. A full Python RAG pipeline from document ingestion through to generation and evaluation. Demonstrates Azure SDK fluency, token-aware chunking, hybrid vector search, confidence routing, and production-grade thinking including the explicit gap between prototype and production.

### 02 — CareAssist Incident Agent

The most compliance-heavy artefact. Demonstrates understanding of regulated industry constraints, human-in-the-loop escalation design, audit trail requirements, and the ability to translate regulatory obligations into technical architecture. Directly relevant to aged care, healthcare, and government technology roles.

### 03 — RetailIQ Sales Agent

The most business-outcome focused artefact. Demonstrates rapid ROI framing, integration with commercial systems (product catalogue, pricing), and multi-channel agent deployment across Teams and web. Relevant to retail, FMCG, and eCommerce technology engagements.

### 04 — AI Governance Advisory Agent

The most complete end-to-end engagement simulation. Documents the full consulting delivery lifecycle — structured discovery with 12 stakeholders, solution design with documented ADRs, UAT with 15 users across five test categories, and a production deployment runbook. The Python backend implements hybrid BM25 + vector search with semantic re-ranking directly against the Azure SDK (no LangChain), with a confidence-gated escalation path built on findings from UAT testing. Every query is logged to a local JSONL file and optionally to SharePoint via the Microsoft Graph API, feeding a Power BI compliance dashboard for the CRO.

Directly relevant to technology consulting, AI practice, and governance-adjacent roles. The use case — using AI to help organisations govern their own AI deployments — reflects what major Microsoft partners are actively building for enterprise clients in 2025–2026.

---

## Design Principles Applied Across All Agents

**Business problem first.** Every agent begins with a clearly framed business problem and a design question. Technology choices are made in service of that problem, not the other way around.

**Human-in-the-loop by default.** All four agents include explicit escalation paths to human review. Automation that fails silently destroys trust. Automation that flags uncertainty builds it.

**Governance is not an afterthought.** Each agent documents data sovereignty, access control, audit requirements, and PII handling as first-class design concerns.

**Production thinking.** Every agent includes a "What I Would Do Differently in Production" section that documents the honest gap between prototype and enterprise deployment.

---

## Infrastructure Pattern

Agents 01–03 share the same Azure infrastructure pattern, deployed via modular Bicep:

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

Agent 04 uses the Azure Python SDK directly rather than Bicep, intentionally demonstrating the layer beneath the infrastructure-as-code abstraction. The `scripts/setup_infrastructure.py` script handles index creation and environment validation programmatically.

---

*Prepared by Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW*
*[linkedin.com/in/arsh-wafiq-khan-chowdhury](https://linkedin.com/in/arsh-wafiq-khan-chowdhury) · [github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury](https://github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury)*

*Portfolio artefacts — methodology demonstration only. All client details fictionalised.*
