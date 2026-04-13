# 03 — DLP Policy Design

**Client:** Ridgeline Partners  
**Author:** Arsh Wafiq Khan Chowdhury  
**Status:** Accepted  

---

## Purpose

This document defines the Data Loss Prevention (DLP) policy applied to Ridgeline Partners' Power Platform environments. It covers the connector classification rationale, the specific groupings applied, and what the policy does and does not prevent.

DLP policies in Power Platform control which connectors can be used together within a single flow or app. They are enforced by the platform at runtime — a flow that violates the policy will be suspended, and a canvas app that breaches the policy cannot be published. They are the primary technical control for preventing makers from inadvertently routing client data to consumer-facing or unapproved services.

---

## Policy Scope

| Environment | Policy applied |
|---|---|
| Development | No DLP policy (intentional — see rationale below) |
| Test | `Ridgeline-Managed-Policy` |
| Production | `Ridgeline-Managed-Policy` |
| Sandbox | No DLP policy |

Development and Sandbox environments are left ungoverned to preserve maker velocity during prototyping. Makers may test connector combinations freely. The DLP boundary is enforced at promotion: a flow that uses a blocked connector combination will be suspended when imported into Test, surfacing the violation before it reaches Production.

This approach was agreed with the CTO during discovery. The alternative — applying the policy in Development — would generate false positives during prototyping and create the perception that governance is obstructing delivery. Ridgeline's makers are technically capable and understand that the policy represents Production intent, not a prohibition on experimentation.

---

## Connector Classification

Power Platform DLP policies classify connectors into three groups. Connectors in the same group can be used together. Connectors in different groups cannot be combined in a single flow or app.

### Business Data Only

These connectors handle corporate data and may be combined freely within this tier.

| Connector | Rationale |
|---|---|
| SharePoint | Core document and data storage |
| Microsoft Dataverse | Primary operational data store |
| Office 365 Outlook | Client and internal communications |
| Microsoft Teams | Internal collaboration and notifications |
| OneDrive for Business | Approved personal file storage |
| Power BI | Reporting and analytics |
| Azure Blob Storage | File processing and archival |
| HTTP with Azure AD | Approved REST calls to internal APIs with authenticated access |
| Microsoft Forms | Data collection |
| Planner | Task management |
| Azure OpenAI | AI inference — internal endpoints only |
| Approvals | Workflow approval management |

### Non-Business Data Only

These connectors handle non-corporate data or connect to external consumer services. They may not be combined with Business Data connectors.

| Connector | Rationale |
|---|---|
| Twitter/X | Social monitoring (marketing use only, no client data) |
| RSS | Feed aggregation for content workflows |
| Bing Maps | Address lookup and visualisation |

### Blocked

These connectors are disabled in Managed Environments regardless of classification.

| Connector | Rationale |
|---|---|
| Gmail | Unapproved external email — client data must not route through personal accounts |
| Dropbox | Unapproved external file storage |
| Google Drive | Unapproved external file storage |
| Salesforce | No Salesforce contract; prevents accidental data routing |
| Slack | Not an approved communication channel; Teams is the standard |
| HTTP (without Azure AD) | Unauthenticated outbound HTTP — permitted only via an approved custom connector |

---

## Key Design Decisions

**HTTP without Azure AD is blocked; HTTP with Azure AD is permitted.** Makers occasionally need to call internal REST APIs or Microsoft Graph endpoints from flows. The `HTTP with Azure AD` connector provides this capability with enforced authentication. Blocking generic HTTP prevents makers from routing data to arbitrary external endpoints without oversight. Any new external endpoint that requires unauthenticated access must be wrapped in a custom connector approved by the platform team.

**Azure OpenAI is in the Business tier.** Ridgeline uses Azure OpenAI for internal document processing workflows. Placing it in the Business tier means it can be combined with SharePoint and Dataverse — the source of documents and structured data — without a DLP violation. This was a deliberate choice; placing it in Non-Business would have blocked the firm's approved AI automation workflows.

**No connector is in both tiers.** Power Platform allows connectors to be unclassified (appearing in neither group). Unclassified connectors default to Non-Business. In Ridgeline's policy, all connectors used in existing solutions are explicitly classified. Unclassified connectors are reviewed quarterly and assigned to a tier or blocked.

**Development has no policy.** This was contested during design. The CTO's position was that applying the policy in Development would slow prototyping for marginal security benefit — any violation will be caught at the Test import stage before it reaches Production. The condition for this decision is that the platform team reviews the weekly admin digest for Test and flags any suspended flows within 48 hours.

---

## Policy Administration

The `Ridgeline-Managed-Policy` is managed by the platform administrator via the Power Platform Admin Centre. Changes to the policy require:

1. A written rationale (added to this document under version history)
2. Review by the Head of Digital and CTO
3. A communication to makers at least 5 business days before the policy change takes effect, to allow any affected flows to be updated

Policy changes that add connectors to the Blocked tier take effect immediately on the effective date. Flows using the newly blocked connector will be suspended in Test and Production. Makers should be given sufficient lead time to transition to an approved alternative.

---

## What DLP Does Not Cover

DLP policies control connector combinations — they do not govern:

- **Data exfiltration within a permitted connector.** A maker with SharePoint access can still share a SharePoint file externally using SharePoint's own sharing features. DLP does not prevent this.
- **Canvas app sharing.** An app can be shared with external users if the maker has permission to do so. App sharing controls are managed through the Maker Access Model (`04_Maker_Access_Model.md`), not DLP.
- **Direct Dataverse API access.** Applications calling Dataverse directly via the Web API are not governed by DLP. Azure Entra ID application registrations with Dataverse access are reviewed as part of the quarterly security review.

These gaps are acknowledged and are compensated for by Managed Environments sharing limits and the maker access model.
