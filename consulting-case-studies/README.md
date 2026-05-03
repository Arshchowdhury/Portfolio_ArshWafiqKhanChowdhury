# Consulting Case Studies

Three end-to-end engagement case studies demonstrating structured discovery, deliberate platform decisions, and delivery discipline. Each starts with a business problem, documents the options evaluated, and traces the outcome back to client constraints rather than technology preferences.

---

| # | Case Study | Domain | Core Problem | Key Technologies |
|---|---|---|---|---|
| [01](./01-room-booking-system/) | Room Booking — Platform Evaluation and Migration | Facilities Management / Co-working | Proposed Power Apps rebuild didn't fit client hardware or licensing constraints | React · Apache · Power Apps evaluation · Azure migration roadmap |
| [02](./02-sales-pipeline-power-bi/) | Sales Pipeline Dashboard — Summit Advisory | Professional Services | Manual Excel exports from Dynamics 365 producing stale, inconsistent pipeline reports | Power BI · Dynamics 365 · DAX · Row-Level Security |
| [03](./03-clearpath-health-intake/) | Digital Intake Automation — Clearpath Health | Healthcare / Community Services | Paper-based patient intake taking 22 minutes per patient with high transcription error rate | Power Apps · Power Automate · Copilot Studio · Azure OpenAI |

---

## What These Case Studies Demonstrate

**Discovery before delivery.** Each engagement begins with structured requirements gathering — SIPOC analysis, stakeholder interviews, gap analysis — before any solution is proposed.

**Platform decisions with documented reasoning.** The room booking engagement recommended *against* the client's preferred platform and documented why. The sales pipeline surfaced that the problem was the data source, not the report format. The health intake engagement uncovered an accessibility requirement that wasn't in the original brief.

**Full delivery traceability.** Requirements, design decisions, implementation approach, and outcomes are documented in each case study. Architecture Decision Records for the most significant technology choices live in [solution-decisions/](../solution-decisions/).
