# Architecture Decision Record
**AI Governance Advisory Agent**
Meridian Advisory Group | Phase 3 of 5

---

This document records the key architectural decisions made during the design phase. Each decision captures the context, the options considered, the decision taken, and the consequences. These records exist to explain design intent to future maintainers and to provide an audit trail of technical choices.

---

## ADR-001: Agent Platform — Copilot Studio vs Azure Bot Framework

**Status:** Accepted

**Date:** Week 2 of engagement

### Context

Meridian requires a conversational AI agent accessible via Microsoft Teams. Two Microsoft-native options were evaluated: Copilot Studio (low-code, Power Platform integrated) and Azure Bot Framework (pro-code, full custom logic).

The delivery team assessed Meridian's internal capability: IT Operations has Power Platform administrators but no .NET or Node.js developers. The engagement has an 8-week timeline.

### Options Considered

| Option | Build effort | Operational ownership | Integration with Teams | Power Automate integration |
|---|---|---|---|---|
| Copilot Studio | Low (visual authoring) | IT Ops can maintain | Native, 3 clicks | Native connector |
| Azure Bot Framework | High (custom code) | Requires developer | Requires Bot Channel registration and custom code | Requires custom HTTP calls |

### Decision

Copilot Studio was selected. The generative answers capability with Azure AI Search as a grounding source meets all functional requirements without custom code. The low-code authoring model allows IT Operations and the AI Practice team to update topics and content without ongoing developer dependency.

### Consequences

**Positive:** Faster delivery. IT Operations can maintain the agent post-handover. Native Power Platform audit logging. Lower total cost of ownership.

**Negative:** Less flexibility for complex multi-step agent reasoning. Copilot Studio topic limits apply (currently 250 topics per agent). Vendor dependency on Microsoft roadmap for generative answers feature evolution.

**Accepted trade-off:** Meridian's use case is well-served by the current Copilot Studio capability set. Complex reasoning is not required at launch. Roadmap risk is acceptable given Microsoft's stated investment in Copilot Studio.

---

## ADR-002: Search Strategy — Hybrid Search vs Pure Keyword vs Pure Vector

**Status:** Accepted

**Date:** Week 2 of engagement

### Context

The knowledge base contains a mix of structured policy documents, regulatory text (EU AI Act), and guidance notes. Users submit queries in natural language that may or may not contain exact terminology from the source documents. The search strategy directly determines the accuracy and relevance of agent responses.

### Options Considered

**Option A: Pure keyword search (BM25)**
Retrieves documents containing exact or near-exact terms from the query. High precision for known terminology (e.g., "Article 13 transparency"), low recall for paraphrased queries (e.g., "what do we need to tell users about our AI system").

**Option B: Pure vector (semantic) search**
Embeds query and documents as vectors. Retrieves semantically similar content regardless of exact wording. Higher recall, but can return plausible-sounding but technically incorrect matches.

**Option C: Hybrid search with semantic ranker**
Runs BM25 and vector search in parallel, fuses results using Reciprocal Rank Fusion, then re-ranks using Azure AI Search's semantic ranker. Combines precision and recall. A confidence threshold (0.7) filters out low-quality matches before they reach the generation step.

### Decision

Hybrid search with semantic ranker was selected (Option C). The 0.7 confidence threshold was set based on testing against a 30-query validation set during the design phase. Queries scoring below 0.7 were found to produce unreliable grounded responses in 4 out of 5 cases. Escalation to SME is preferable to a low-confidence generated answer in a compliance context.

### Consequences

**Positive:** Best retrieval accuracy across both regulatory text (exact terminology) and paraphrased queries. Confidence threshold provides a safety valve that routes uncertain queries to a human expert.

**Negative:** Semantic ranker requires a Standard tier Azure AI Search resource (higher cost than Basic). Nightly index refresh means documents added during the day are not immediately searchable.

**Accepted trade-off:** The Standard tier cost is within budget. Nightly refresh is acceptable given the low frequency of knowledge base updates (monthly per the agreed operating model).

---

## ADR-003: Knowledge Base Storage — SharePoint Online vs Azure Blob Storage vs Azure AI Search Native

**Status:** Accepted

**Date:** Week 2 of engagement

### Context

The knowledge base documents need to be stored in a location that: (a) IT Operations and the AI Practice team can manage without developer involvement, (b) integrates natively with Azure AI Search indexing, and (c) inherits Meridian's existing access control model.

### Options Considered

**Option A: SharePoint Online Document Library**
Documents uploaded and managed via the familiar SharePoint interface. Native Azure AI Search connector available. Inherits M365 permissions. IT Operations and AI Practice can manage without IT tickets.

**Option B: Azure Blob Storage**
Technically simple for AI Search indexing. Requires Azure Storage account management. No familiar UI for non-technical staff to manage documents. Custom access control required.

**Option C: Azure AI Search native document store**
Not available as a user-facing document store. AI Search is a search index, not a document repository. Not a valid option.

### Decision

SharePoint Online Document Library was selected (Option A). The native AI Search SharePoint connector handles indexing. The familiar SharePoint interface means the AI Practice team can add, update, and retire documents without any developer or IT Operations involvement. M365 permissions model is already configured and understood.

### Consequences

**Positive:** Non-technical staff can manage the knowledge base. No additional infrastructure to maintain. Inherits existing DLP and compliance policies. SharePoint versioning provides document history.

**Negative:** SharePoint connector for AI Search has known limitations: it does not support incremental indexing of document metadata changes (only content changes trigger re-index). Maximum document size is 16MB (sufficient for all current documents).

**Accepted trade-off:** Metadata-only changes are uncommon in this use case. Document size constraint is not a risk given current library contents.

---

## ADR-004: Audit Logging — Power Automate vs Copilot Studio Analytics vs Azure Application Insights

**Status:** Accepted

**Date:** Week 3 of engagement

### Context

Every agent interaction must be logged for compliance purposes. The log must be structured (queryable, reportable) and retained for 7 years. The logging mechanism must not depend on ongoing developer support.

### Options Considered

**Option A: Power Automate flow triggered by Copilot Studio**
Copilot Studio calls a Power Automate HTTP trigger at the end of each interaction. Power Automate writes a structured record to a SharePoint List. Manageable by Power Platform administrators. Data stays in the Meridian M365 tenant.

**Option B: Copilot Studio native analytics**
Built-in analytics in the Copilot Studio portal. Limited field customisation. Data is held in Dataverse (requires Dataverse licence). No direct export to Power BI without additional configuration. Retention policy controlled by Microsoft, not Meridian.

**Option C: Azure Application Insights**
Requires custom telemetry instrumentation. Pro-code integration. No native Copilot Studio connector. Data held in Azure Monitor workspace. Complex to query for non-technical compliance staff.

### Decision

Power Automate with SharePoint List was selected (Option A). This gives Meridian full control over the audit schema, retention policy, and data residency. The SharePoint List is directly readable by Power BI without additional transformation. IT Operations and Compliance staff can query and export records without developer involvement.

### Consequences

**Positive:** Full schema control. Data in M365 tenant with existing DLP controls. Direct Power BI connectivity. 7-year retention achievable via SharePoint retention policy. No additional licensing beyond existing Power Platform entitlements.

**Negative:** Power Automate flow introduces a small latency (~1 to 2 seconds) at the end of each interaction. SharePoint List has a 5,000 item view threshold (requires indexed columns and filtered views for lists exceeding this volume).

**Accepted trade-off:** 1 to 2 second logging latency is imperceptible to users. SharePoint List indexing is configured on the Timestamp and UserUPN columns from initial deployment to handle future volume.

---

## ADR-005: Reporting — Power BI vs SharePoint List Views vs Dataverse Analytics

**Status:** Accepted

**Date:** Week 3 of engagement

### Context

The CRO requires a compliance dashboard showing interaction volume, escalation rate, and query topic distribution. The dashboard must be accessible to Risk and Compliance staff without requiring SharePoint List query skills.

### Options Considered

**Option A: Power BI with SharePoint List connector**
Rich visualisation. Scheduled refresh. Familiar to Meridian's Finance and Risk teams who already use Power BI. Shares via Power BI Service (M365 integrated).

**Option B: SharePoint List views and calculated columns**
No additional tooling. Limited to tabular views. No charting or trend analysis. Insufficient for CRO compliance reporting needs.

**Option C: Dataverse analytics and model-driven app**
Requires Dataverse. Not in scope for this engagement's licensing model.

### Decision

Power BI was selected (Option A). The CRO confirmed that Meridian's Risk team already uses Power BI for other compliance reporting, so the tool is familiar and the workspace access model is already established.

### Consequences

**Positive:** Rich dashboards. Familiar tool. Scheduled refresh keeps compliance data current. Shareable via Power BI Service with AAD-based access control.

**Negative:** Requires Power BI Pro licence for report authors and dashboard consumers who are not E5 licensed. Four-hour scheduled refresh means dashboard data lags the audit list by up to four hours.

**Accepted trade-off:** Power BI Pro licences for four Risk and Compliance staff are within budget. Four-hour data lag is acceptable for compliance reporting (not a real-time operational dashboard).

---

## Decision Log Summary

| ADR | Decision | Date | Status |
|---|---|---|---|
| ADR-001 | Copilot Studio over Azure Bot Framework | Week 2 | Accepted |
| ADR-002 | Hybrid search with 0.7 confidence threshold | Week 2 | Accepted |
| ADR-003 | SharePoint Online document library as knowledge base | Week 2 | Accepted |
| ADR-004 | Power Automate with SharePoint List for audit logging | Week 3 | Accepted |
| ADR-005 | Power BI for compliance reporting | Week 3 | Accepted |

---

*Document version 1.0. Prepared by Arsh Chowdhury, Technology Consultant. Simulated engagement for portfolio purposes.*
