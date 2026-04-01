# Discovery and Requirements
**AI Governance Advisory Agent**
Meridian Advisory Group | Phase 1 of 5

---

## Project Background

Meridian Advisory Group is a mid-sized professional services firm with 420 staff across Legal, Risk, and Strategy practices. Following the EU AI Act coming into force and increasing client demand for AI governance advisory services, the firm needed its knowledge workers to rapidly access up-to-date regulatory guidance without relying on a small team of AI specialists.

The firm's existing approach involved email-based queries routed to two senior consultants, creating bottlenecks, inconsistent answers, and no audit trail for compliance purposes.

---

## Problem Statement

Knowledge workers at Meridian spend an average of 47 minutes per week searching for AI governance guidance across scattered documents, email threads, and external websites. Response times from internal specialists average 2.4 business days. There is no centralised record of what guidance was given, to whom, or on what basis.

This creates three categories of risk:

- **Operational risk** from inconsistent guidance reaching clients
- **Compliance risk** from the absence of an audit trail under the EU AI Act Article 13 transparency obligations
- **Reputational risk** from delayed or incorrect advice in a fast-moving regulatory environment

---

## Stakeholder Analysis

| Stakeholder | Role | Interest |
|---|---|---|
| Elena Marchetti | Chief Risk Officer | Sponsor. Audit trail and compliance assurance. |
| Daniel Soh | Head of AI Practice | Subject matter expert. Accuracy of policy content. |
| Sarah Kim | Senior Consultant | Primary end user. Speed and ease of access. |
| IT Operations | Infrastructure | Security posture, M365 integration, environment management. |
| Legal and Compliance | Risk | Data handling, access controls, record retention. |

---

## Current State Pain Points

Workshops with Meridian staff (12 participants across three sessions) surfaced the following prioritised pain points:

**High priority**
- No single source of truth for AI governance policies
- Specialist availability creates single points of failure
- Guidance given verbally leaves no compliance record

**Medium priority**
- EU AI Act documents distributed across SharePoint, email attachments, and an external knowledge base
- Onboarding new consultants takes 3 to 4 weeks before they can independently answer basic governance questions
- No visibility into what questions are being asked most frequently

**Low priority**
- Formatting inconsistencies across policy documents
- No version control on internal policy documents

---

## Business Requirements

### Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Users must be able to submit natural language governance queries via Microsoft Teams | Must have |
| FR-002 | The agent must return a response with cited source documents within 10 seconds | Must have |
| FR-003 | All interactions must be logged with user, query, response, and timestamp | Must have |
| FR-004 | Queries outside the agent scope must trigger a named SME escalation pathway | Must have |
| FR-005 | The knowledge base must be updatable by authorised staff without developer involvement | Must have |
| FR-006 | A compliance dashboard must display interaction volume, escalation rate, and query topics | Should have |
| FR-007 | The agent must support at minimum 50 concurrent users without degradation | Should have |
| FR-008 | Responses must indicate the confidence level of the answer | Could have |

### Non-functional Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | Response latency (P95) | Under 10 seconds |
| NFR-002 | System availability | 99.5% during business hours AEST |
| NFR-003 | Data residency | Australia East region |
| NFR-004 | Access control | Role-based via Azure Active Directory |
| NFR-005 | Audit log retention | Minimum 7 years (aligned to client record obligations) |
| NFR-006 | Document currency | Knowledge base reviewable and updatable monthly |

---

## Success Criteria

The engagement will be considered successful when:

1. Time to answer a standard governance query drops below 60 seconds
2. 80% of queries are resolved without specialist escalation within 90 days of go-live
3. 100% of interactions are captured in the audit log
4. Zero unrecorded guidance events within the first compliance review cycle
5. CRO sign-off on the compliance dashboard as fit for regulatory evidence purposes

---

## Scope

### In Scope

- Copilot Studio agent deployed to Microsoft Teams
- Azure AI Search index connected to SharePoint knowledge base
- Knowledge base seeded with EU AI Act full text, Meridian internal AI policy, and 12 priority guidance documents
- Power Automate flow for audit logging to SharePoint List
- Power BI compliance dashboard connected to audit list
- Three Power Platform environments: Development, Test, Production
- UAT with 15 business users across Legal and Risk practices
- Deployment runbook and handover to IT Operations

### Out of Scope

- Integration with external legal databases (Lexis, Westlaw)
- Multi-language support (English only at launch)
- Mobile app or web portal (Teams only at launch)
- Document authoring or editing capabilities within the agent
- Automated document ingestion pipelines from email or external feeds

---

## Assumptions

- Meridian has an active Microsoft 365 E3 or E5 licence with Copilot Studio entitlements
- Azure subscription available in Australia East region
- IT Operations will manage environment provisioning with guidance from the delivery team
- Subject matter experts (Daniel Soh and one delegate) are available for 2 hours per week during the build phase for content review
- All knowledge base documents are cleared for internal use and do not contain client-confidential material

---

## Constraints

- Delivery timeline: 8 weeks from kick-off to Production go-live
- Budget: Fixed-fee engagement. No infrastructure cost overruns.
- The Default Power Platform environment must not be used (per IT Operations policy)
- No direct database access from the agent. All data retrieval via AI Search.

---

## Sign-off

| Name | Role | Date |
|---|---|---|
| Elena Marchetti | Chief Risk Officer | Week 1 |
| Daniel Soh | Head of AI Practice | Week 1 |
| IT Operations Lead | Infrastructure | Week 1 |

---

*Document version 1.0. Prepared by Arsh Chowdhury, Technology Consultant. Simulated engagement for portfolio purposes.*
