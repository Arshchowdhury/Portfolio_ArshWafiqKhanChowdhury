# ADR 003 — SharePoint over Dataverse for Healthcare Intake System

**Status:** Accepted
**Date:** March 2026
**Context:** Clearpath Health digital patient intake automation

---

## Context

Clearpath Health required a data layer for the digital patient intake system — storing intake form submissions, patient records, consent logs, and staff review queues. The solution was built on Power Apps and Power Automate within an existing Microsoft 365 Business Standard environment. The choice between SharePoint and Dataverse was the primary data architecture decision.

---

## Decision

Use SharePoint Online as the data layer, with structured lists and column-level permissions, rather than Microsoft Dataverse.

---

## Options Considered

**Option 1: SharePoint Online (chosen)**
- Pros: Included in M365 Business Standard licence (no additional cost); familiar to operations staff; good Power Automate integration; audit trail and version history built in; column-level permissions for PII control; 7-year retention configurable via retention policies
- Cons: Not a relational database; limited to SharePoint list item thresholds (5,000 item default view limit, addressable with indexed columns); less suitable for complex relational data models

**Option 2: Microsoft Dataverse**
- Pros: Full relational database capabilities; row-level security; native integration with model-driven Power Apps; better for complex data relationships; enterprise-grade audit trail
- Cons: Requires Power Apps per-user or Power Platform licences beyond M365 Business Standard; significantly higher cost at this client's user count; implementation complexity beyond what the engagement warranted

**Option 3: Azure SQL Database**
- Pros: Full relational database; scalable; enterprise-ready
- Cons: Requires Azure subscription and ongoing management; HTTP connector overhead in Power Automate; outside scope for a client with no Azure footprint in Phase 1

---

## Rationale

The client's intake data model was not deeply relational — the core entity was an intake record with a set of structured fields, a consent log entry, and a status flag. This is well within SharePoint's capabilities.

Dataverse would have been the right choice if the engagement required model-driven apps, complex relational queries across multiple entities, or row-level security at the record level. None of those requirements were present.

The Aged Care Act compliance requirement (7-year record retention) was addressable through SharePoint's retention policy configuration. The consent log required an immutable audit trail — SharePoint's version history and restricted permissions for the consent list met this requirement.

---

## Consequences

- No additional licensing cost beyond existing M365 Business Standard
- Indexed columns configured on all high-frequency query paths to mitigate SharePoint threshold limits
- Consent log list has restricted delete permissions (append-only via Power Automate; no manual delete)
- If patient volume exceeds 3,000 intakes/month or relational complexity increases, migration to Dataverse or Azure SQL is the defined next step

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant*
