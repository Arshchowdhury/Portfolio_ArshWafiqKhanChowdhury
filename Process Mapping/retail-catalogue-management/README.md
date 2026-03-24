# Process Mapping: Retail Product Catalogue Management
## Current State → Future State 
## Manual Catalogue to Automated Digital Workflow

**Author:** Arsh Wafiq Khan Chowdhury - Technology Consultant, Sydney NSW
**Date:** March 2026
**Classification:** Portfolio artefact - original design. Client details fictionalised.

---

## Business Context

### Client Scenario

**Organisation:** Meridian Home & Living (Fictionalised)
**Sector:** Specialty retail — home furnishings and lifestyle products
**Size:** 12 stores across NSW and VIC, eCommerce site, ~180 SKUs updated per month
**Problem:** Product catalogue changes — new product launches, price updates, and discontinued items — are managed through a combination of email chains, Excel spreadsheets, and manual data entry across three disconnected systems: the eCommerce platform, the in-store POS system, and the sales team's product reference sheets.

The result is a catalogue that is routinely out of sync. Customers encounter incorrect prices online, sales staff quote outdated specifications, and store managers manually reconcile discrepancies at end of week.

### Business Objectives

1. Establish a single source of truth for all product catalogue data
2. Eliminate manual re-entry of product changes across multiple systems
3. Ensure eCommerce, POS, and sales team materials are updated within 2 hours of approval
4. Create an auditable change history for pricing and product decisions
5. Reduce catalogue-related customer complaints and staff time spent on corrections

---

## Current State Process

### Pain Points Identified (Discovery Workshop)

| # | Pain Point | Impact | Frequency |
|---|---|---|---|
| 1 | Product changes submitted via email — no structured format | Incomplete data, missing fields, downstream errors | Every change |
| 2 | Catalogue Manager manually re-enters data across 3 systems | ~4 hours per week of duplicate data entry | Weekly |
| 3 | No approval workflow — changes sometimes go live without sign-off | Pricing errors, compliance risk | Monthly |
| 4 | eCommerce and POS updates done separately with no sync | Price discrepancies between channels | Weekly |
| 5 | No audit trail — impossible to determine who approved a price change | Accountability gap, finance risk | On demand |
| 6 | Sales team product sheets updated manually via emailed PDFs | Sales staff quoting wrong specs or discontinued products | Weekly |

### Current State Process Map

![Current State](https://raw.githubusercontent.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury/main/Process%20Mapping/retail-catalogue-management/01-current-state.svg)



---

**Key issues highlighted:**
- No structured submission — email with free-form content
- Triple manual data entry across three systems
- No formal approval workflow for pricing
- No audit trail or change history
- Sales staff reliant on emailed PDFs that may be outdated

---

## Gap Analysis

| Capability | Current State | Gap | Future State Requirement |
|---|---|---|---|
| Change submission | Free-form email | Unstructured, incomplete, no validation | Structured digital form with mandatory field validation |
| Approval workflow | Informal email review | No audit trail, no escalation | Formal approval routing with timestamps and sign-off |
| System updates | Manual re-entry ×3 | Time-consuming, error-prone | Single entry, automated propagation to all systems |
| Price change governance | Ad hoc Finance review | No formal sign-off, compliance risk | Mandatory Finance approval with audit log |
| Sales team updates | Manual PDF emails | Outdated materials, no version control | Real-time SharePoint product reference with notifications |
| Change history | None | No accountability, no rollback capability | Full audit trail in SharePoint with version history |
| Cross-channel sync | Manual | eCommerce and POS routinely out of sync | Automated sync within 2 hours of approval |

---

## Future State Process

### Solution Architecture Summary

| Component | Technology | Purpose |
|---|---|---|
| Change submission | Power Apps (Canvas) | Structured product change form with mandatory validation and image upload |
| Approval routing | Power Automate | Automated approval workflow with role-based routing and escalation |
| Single source of truth | SharePoint Online List | Master product catalogue with full version history and audit trail |
| eCommerce sync | Power Automate + Shopify API | Auto-pushes approved changes to Shopify within 2 hours |
| POS sync | Power Automate + Lightspeed API | Auto-pushes approved changes to Lightspeed POS |
| Sales reference | SharePoint Document Library | Auto-generated product sheets, real-time notifications to store Teams channels |
| Reporting | Power BI | Catalogue change volume, approval turnaround times, error rates |
| AI assist (optional) | Azure OpenAI | Product description generation and SEO tag suggestions for new listings |

### Future State Process Map

![Future State](https://raw.githubusercontent.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury/main/Process%20Mapping/retail-catalogue-management/02-future-state.svg)



---

## Process Improvement Summary

| Metric | Current State | Future State | Improvement |
|---|---|---|---|
| Time to update all channels | 4–24 hours | < 2 hours | ~90% reduction |
| Data entry touchpoints | 3 manual entries | 1 entry, automated propagation | 3× reduction in manual effort |
| Catalogue Manager time on updates | ~4 hrs/week | ~30 min/week (exception handling only) | ~87% reduction |
| Price change approval audit trail | None | Full timestamped log in SharePoint | Full compliance |
| Channel sync reliability | ~70% (discrepancies common) | ~100% (automated) | Fully consistent |
| Sales staff product reference currency | 24–72 hours lag | Real-time via SharePoint + Teams | Same-day |

---

## User Stories

| # | As a... | I want to... | So that... |
|---|---|---|---|
| US-01 | Buyer | Submit product changes via a structured form | My request contains all required information without back-and-forth emails |
| US-02 | Finance Manager | Receive and action price change approvals in Teams | I can approve changes quickly without switching systems |
| US-03 | Catalogue Manager | See all pending and completed changes in one dashboard | I have visibility without checking multiple systems |
| US-04 | Store Manager | Receive instant notifications when a product changes | My team is never quoting outdated prices or specs |
| US-05 | Operations Director | View approval turnaround times and change volumes | I can identify bottlenecks and optimise the process |
| US-06 | Buyer | See the current status of a submitted change request | I know where it is in the workflow without emailing the Catalogue Manager |

---

## Acceptance Criteria (Sample — US-01)

**Given** a Buyer opens the Product Change Request form in Power Apps
**When** they attempt to submit without completing all mandatory fields
**Then** the form should display inline validation errors and prevent submission

**Given** a Buyer completes all mandatory fields and submits
**When** the form is submitted successfully
**Then** a confirmation screen should display a reference number, and a Teams notification should be sent to the Buyer confirming receipt within 60 seconds

**Given** a Price Change request is submitted
**When** the Power Automate workflow triggers
**Then** a Finance Manager approval request should appear as a Teams adaptive card within 5 minutes of submission

---

## Implementation Approach

### Phase 1 — Foundation (Weeks 1–3)
- SharePoint master catalogue list schema design
- Power Apps change request form — mandatory fields, validation, image upload
- Basic Power Automate approval routing — Finance and Merchandise Manager flows
- UAT with Buyer, Catalogue Manager, and Finance Manager

### Phase 2 — System Integration (Weeks 4–7)
- Shopify API integration via Power Automate custom connector
- Lightspeed POS API integration
- Automated Teams channel notifications to stores
- End-to-end integration testing across all channels

### Phase 3 — Reporting and Optimisation (Weeks 8–10)
- Power BI catalogue management dashboard
- Azure OpenAI product description assist (optional feature)
- Go-live with all 12 stores
- 30-day post-launch review

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shopify API rate limits causing update delays | Low | Medium | Implement queuing and retry logic in Power Automate flows |
| Finance Manager approval bottleneck | Medium | High | Escalation rule: auto-approve if no response within 4 hours, notify Director |
| Staff resistance to new submission process | Medium | Medium | Champion programme — one power user per buying team, training in Week 1 |
| API breaking changes from Shopify or Lightspeed | Low | High | Version-lock API calls, monitor vendor release notes |

---

## Related Portfolio Artefacts

- [RetailIQ — AI Sales Assistant Agent](../Ai-Agent-Design/RetailIQ-AI-Agent/) — AI agent design built on the same retail domain, handling customer and staff product queries using the catalogue as the knowledge base
- [Workflow Automation Case Study](../Workflow-Automation-Case-Studies/Automated-Document-Processing/) — related automation design pattern using Power Automate and Azure OpenAI

---

*Prepared by Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW*
*arshwafiq@gmail.com · [linkedin.com/in/arsh-wafiq-khan-chowdhury](https://linkedin.com/in/arsh-wafiq-khan-chowdhury)*
*[github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury](https://github.com/Arshchowdhury/Portfolio_ArshWafiqKhanChowdhury)*
