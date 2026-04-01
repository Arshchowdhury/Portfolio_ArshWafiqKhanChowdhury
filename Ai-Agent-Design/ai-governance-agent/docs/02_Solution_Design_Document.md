# Solution Design Document
**AI Governance Advisory Agent**
Meridian Advisory Group | Phase 2 of 5

---

## Executive Summary

This document defines the technical and functional design for the AI Governance Advisory Agent delivered to Meridian Advisory Group. The solution is built on Microsoft Power Platform and Azure AI Services, deployed entirely within the Meridian Microsoft 365 and Azure tenant. It provides knowledge workers with instant, cited, audited access to AI governance policy via a Microsoft Teams chat interface.

The agent uses a Retrieval Augmented Generation (RAG) pattern: when a user submits a query, Azure AI Search retrieves the most relevant document chunks from the SharePoint knowledge base, which Copilot Studio uses to generate a grounded, cited response. Every interaction is logged to a SharePoint audit list via Power Automate. Power BI provides a compliance and usage dashboard for the Risk team.

---

## Solution Overview

| Component | Service | Purpose |
|---|---|---|
| Agent interface | Copilot Studio | Natural language query handling, topic routing, RAG integration |
| User channel | Microsoft Teams | Entry point for all knowledge worker queries |
| Search and retrieval | Azure AI Search | Hybrid keyword and semantic search across the knowledge base |
| Knowledge base | SharePoint Online | Document library storing all AI governance content |
| Audit logging | Power Automate | Triggered flow recording every interaction to the audit list |
| Audit store | SharePoint List | Structured record of all queries, responses, timestamps, and users |
| Compliance reporting | Power BI | Dashboard for the Risk team with usage, escalation, and topic analytics |
| Identity and access | Azure Active Directory | Authentication and RBAC across all services |

---

## Architecture

The solution follows a hub-and-spoke pattern with Copilot Studio at the centre. All external service calls are made by Copilot Studio or Power Automate. Users interact only through Microsoft Teams. No service is publicly exposed.

See `architecture.svg` in this directory for the full solution architecture diagram.

### Data Flow

1. A user submits a natural language query via the Teams channel connected to the Copilot Studio agent.
2. Copilot Studio evaluates the query against configured topics. Queries within scope are routed to the generative answers node. Out-of-scope queries trigger the escalation pathway.
3. The generative answers node calls Azure AI Search with the user query. AI Search performs a hybrid query (keyword BM25 plus semantic vector search) against the indexed knowledge base.
4. AI Search returns the top ranked document chunks above the 0.7 semantic confidence threshold. Chunks below this threshold are excluded from the response.
5. Copilot Studio generates a response grounded in the retrieved chunks, including citation links back to the source SharePoint documents.
6. The response is returned to the user in Teams. If no chunks meet the confidence threshold, the agent escalates to the named SME (Daniel Soh) with the original query forwarded via Teams notification.
7. On every response (whether generated or escalated), Copilot Studio triggers the Power Automate audit flow.
8. Power Automate writes a record to the SharePoint Audit List including: User UPN, timestamp, query text, response summary, source documents cited, confidence band (High / Medium / Escalated), and session ID.
9. Power BI reads the SharePoint Audit List on a scheduled refresh and updates the compliance dashboard.

---

## Component Design

### Copilot Studio Agent

**Topics configured:**

| Topic | Description | Trigger phrases |
|---|---|---|
| EU AI Act Inquiry | Questions about specific EU AI Act articles, obligations, or timelines | article, obligation, high risk, prohibited, GPAI, transparency |
| Risk Classification | Questions about how to classify an AI system by risk category | classify, risk level, tier, category, assessment |
| Corporate Policy | Questions about Meridian internal AI usage policies | policy, approved, prohibited tool, internal, staff |
| Escalation | Queries outside agent scope or below confidence threshold | Agent-triggered (not user phrase) |
| Greeting and Scope | Introduction and scope statement when agent is first opened | hello, hi, what can you do, help |

**Generative answers configuration:**
- Source: Azure AI Search custom connector
- Grounding strictness: Strict (responses must be grounded in retrieved content only)
- Citation format: Inline footnote with document title and SharePoint URL
- Fallback behaviour: Escalate to SME when no content meets the 0.7 confidence threshold

**Escalation pathway:**
When the agent escalates, it sends a Teams adaptive card to Daniel Soh (Head of AI Practice) containing the user's original query, the session ID for audit traceability, and a prompt to respond directly to the user within one business day.

### Azure AI Search

**Index configuration:**

| Setting | Value |
|---|---|
| Index name | meridian-ai-governance |
| Data source | SharePoint Online connector (Documents library) |
| Indexing schedule | Nightly at 02:00 AEST |
| Semantic configuration | Enabled (australiaeast region) |
| Semantic ranker model | Default (Microsoft) |
| Confidence threshold applied in Copilot | 0.7 (configurable) |
| Chunk size | 512 tokens with 20% overlap |
| Fields indexed | title, content, lastModifiedDate, author, sourceUrl |

**Hybrid search approach:** Every query executes both BM25 keyword retrieval and semantic vector retrieval in parallel. Results are fused using Reciprocal Rank Fusion (RRF). The semantic ranker then re-scores the fused results. Only chunks scoring above 0.7 on the semantic score are passed to Copilot Studio for grounding.

### SharePoint Knowledge Base

**Document library structure:**

```
AI-Governance-KB/
  EU-AI-Act/
    EU_AI_Act_FullText_April2024.pdf
    EU_AI_Act_Summary_Obligations.docx
    GPAI_Model_Code_of_Practice_v1.docx
  Meridian-Policy/
    Meridian_AI_Usage_Policy_v2.docx
    Meridian_AI_Risk_Classification_Guide.docx
    Approved_AI_Tools_Register.xlsx
  Guidance-Notes/
    [12 priority guidance documents]
```

**Access control:** Read access granted to all Meridian staff (via AAD group). Write and upload access restricted to the AI Practice team (Daniel Soh and two delegates).

**Version control:** SharePoint native versioning enabled. AI Search re-indexes modified documents on the nightly schedule. Document owners are responsible for retiring outdated versions.

### Power Automate Audit Flow

**Trigger:** HTTP request from Copilot Studio on each completed interaction.

**Flow steps:**
1. Receive HTTP POST from Copilot Studio containing the interaction payload (JSON)
2. Parse JSON to extract required fields
3. Create item in the SharePoint Audit List
4. Respond 200 OK to Copilot Studio
5. If confidence band is Escalated, send Teams notification to Daniel Soh (parallel branch)

**Audit record schema:**

| Field | Type | Source |
|---|---|---|
| SessionID | Text | Copilot Studio session variable |
| UserUPN | Text | Authenticated user identity |
| Timestamp | DateTime | Flow execution time (UTC) |
| QueryText | Text | User message content |
| ResponseSummary | Text | First 500 characters of agent response |
| SourceDocuments | Text (multi) | Citation titles returned by AI Search |
| ConfidenceBand | Choice | High / Medium / Escalated |
| EscalatedTo | Text | SME name if escalated, blank otherwise |
| EnvironmentName | Text | Dev / Test / Production |

### Power BI Compliance Dashboard

**Data source:** SharePoint List connector (scheduled refresh, every 4 hours during business hours).

**Dashboard pages:**

1. **Overview** showing total query volume, escalation rate, and average confidence band for the selected period
2. **Topic distribution** showing breakdown of query types across the five configured topics
3. **Escalation log** showing a filterable table of all escalated interactions with query text and SME assignment
4. **User activity** showing query volume by user (anonymisable for privacy reporting) and time of day heatmap

**Access:** CRO and Head of AI Practice have full dashboard access. IT Operations has read access for support purposes. Individual user records are accessible only to Compliance and Risk roles.

---

## Security Design

**Authentication:** All services authenticate via Azure Active Directory. No service accounts with stored passwords. Managed identities used where supported (Power Automate connectors use service principal).

**Data handling:** No user query data leaves the Meridian tenant. Azure AI Search, SharePoint, and Power BI all run within the Meridian Azure subscription (Australia East). Copilot Studio is provisioned in the Meridian Power Platform environment.

**Access control matrix:**

| Role | Copilot (Teams) | Knowledge Base | Audit List | Dashboard |
|---|---|---|---|---|
| All staff | Query only | Read | No access | No access |
| AI Practice | Query only | Read and write | Read | Full access |
| Risk and Compliance | Query only | Read | Read | Full access |
| IT Operations | Admin | Read | Read | Read |

**Network:** No public endpoints. All Power Platform and Azure services communicate within the Microsoft backbone network. SharePoint and Teams are already within the Meridian M365 boundary.

---

## Environment Strategy

Three environments are provisioned. The Default environment is not used.

| Environment | Purpose | Data |
|---|---|---|
| Development | Active build and testing | Synthetic test data only |
| Test | UAT and pre-release validation | Anonymised production-like data |
| Production | Live service | Real Meridian staff and audit data |

Promotion from Development to Test requires peer review. Promotion from Test to Production requires CRO sign-off and a completed UAT sign-off document.

---

## Open Items and Risks

| ID | Item | Owner | Status |
|---|---|---|---|
| OI-001 | Confirm AI Search semantic ranker availability in Australia East for the Meridian subscription tier | IT Operations | Open |
| OI-002 | Confirm Power Automate connection licensing for SharePoint write operations | IT Operations | Open |
| OI-003 | Legal review of storing query text in audit list (employee monitoring obligations under Australian law) | Legal and Compliance | Open |
| RISK-001 | Knowledge base documents contain outdated guidance. Risk: agent provides incorrect advice. Mitigation: monthly review cadence, document owner assigned per folder. | Daniel Soh | Mitigated |
| RISK-002 | Copilot Studio generative answers hallucinate beyond retrieved content. Mitigation: grounding strictness set to Strict, no off-topic generation permitted. | Delivery team | Mitigated |

---

*Document version 1.0. Prepared by Arsh Chowdhury, Technology Consultant. Simulated engagement for portfolio purposes.*
