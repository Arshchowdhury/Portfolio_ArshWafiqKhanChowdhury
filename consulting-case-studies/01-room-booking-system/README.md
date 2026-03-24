# Case Study 01 — Room Booking System: Platform Evaluation and Web Migration

> **Live engagement. Client details anonymised.**

**Industry:** Facilities Management / Co-working
**Stack:** React, HTML/CSS/JavaScript, Apache (local server) → Azure migration roadmap
**Engagement type:** Technology evaluation, platform recommendation, custom web implementation, cloud architecture planning

---

## Context

A Sydney-based co-working operator had an existing web-based room booking system that had become difficult to maintain and visually dated. The CEO proposed migrating to Microsoft Power Apps as the modernisation path, citing its low-code appeal and integration with the organisation's existing Microsoft 365 licences.

I was brought in to evaluate the proposed approach and lead the implementation. The evaluation concluded that Power Apps was not the right fit for this use case. A custom React web application — hosted on the client's existing local server — was recommended and built instead, with a documented Azure migration roadmap for the client's next growth phase.

---

## The Problem

The existing system was a web-based booking tool that staff had outgrown. Core issues included:

| Issue | Detail |
|---|---|
| No real-time availability | Booking state was not updated live; double bookings required manual resolution |
| No cancellation workflow | Members messaged front-desk directly; the system had no cancellation mechanism |
| Admin had no override controls | Rooms couldn't be blocked for maintenance without removing them from the system entirely |
| Poor mobile experience | The existing interface was not responsive; tablet use at front-desk was frustrating |
| Maintenance dependency | Any change to the system required developer involvement |

The CEO's proposed solution was to rebuild on Power Apps, reasoning that M365 licences were already in place and a low-code platform would reduce ongoing maintenance costs.

---

## Platform Evaluation

Before committing to any build, I ran a structured evaluation of Power Apps against the client's specific requirements and constraints.

### Power Apps Assessment

| Criterion | Finding |
|---|---|
| Performance on front-desk hardware | Canvas apps load the full Power Apps runtime on each session; testing on the client's front-desk tablets showed 8–12 second load times — unacceptable for a high-frequency front-desk tool |
| Licensing for casual users | Power Apps per-user licences apply to every user who accesses the app. The client had part-time casual staff and visiting members who would use the system irregularly — the per-user model added significant cost at scale |
| UI flexibility for custom UX requirements | Canvas app layout is constrained by the grid system and available controls. The client's front-desk had specific UX needs (high-contrast mode for glare, minimal-tap workflows under time pressure) that would have required significant workarounds |
| Offline / low-connectivity support | The co-working space had patchy WiFi in several areas. Power Apps canvas apps have no offline capability in this configuration |
| Future migration path | Power Apps creates a degree of platform lock-in. A custom web application could be containerised and moved to Azure App Service with significantly less effort |
| Maintenance post-handover | Power Apps does reduce maintenance overhead for simple CRUD apps — this is a genuine strength of the platform |

**Conclusion:** Power Apps is well-suited to internal workflow automation, model-driven apps backed by Dataverse, and environments where all users hold M365 licences and low-code maintainability is the primary priority. For a front-desk booking tool with performance constraints, occasional external users, and specific UX requirements, the trade-offs did not stack up. The recommendation was documented and presented to the CEO before any build commenced.

> Power Apps remains a tool I work with regularly for the use cases it fits well — internal workflow apps, Dynamics 365 extensions, and Dataverse-backed model-driven applications. The evaluation here was a requirements-driven decision, not a preference.

---

## Discovery

### SIPOC

| | S — Suppliers | I — Inputs | P — Process | O — Outputs | C — Customers |
|---|---|---|---|---|---|
| | Members, front-desk staff, operations management | Booking requests, room availability, member roster | Booking request → availability check → confirmation → communication | Booking confirmation, room assignment, cancellation notice, utilisation data | Members, front-desk staff, operations manager |

**Scope boundary:** Process starts when a member initiates a booking request. Process ends when confirmation is received or the conflict is resolved.

---

### Requirements Register

Requirements were gathered from discovery workshops with front-desk staff, the operations manager, and member feedback. The CEO's original Power Apps brief was used as a starting point; requirements were then validated independently against observed user behaviour.

| ID | Requirement | Priority | Source | Notes |
|---|---|---|---|---|
| REQ-01 | System must load to a usable state within 2 seconds on existing front-desk hardware | Must Have | Staff observation | Direct response to observed performance issue |
| REQ-02 | No per-user licensing cost for casual or infrequent users | Must Have | Operations Manager | Power Apps per-user model flagged as cost risk |
| REQ-03 | Booking creation must validate against real-time availability and prevent overlap | Must Have | Front-desk staff | Core functional requirement |
| REQ-04 | Admin must be able to block rooms for maintenance without affecting member-facing view | Must Have | Operations Manager | Not supported in previous system |
| REQ-05 | Members must be able to self-cancel bookings in real time | Must Have | Front-desk staff | Previously handled manually |
| REQ-06 | System must be maintainable by non-developers for content changes | Must Have | Operations Manager | Key driver behind CEO's original Power Apps proposal |
| REQ-07 | High-contrast mode for front-desk display | Must Have | Front-desk staff | Glare from large window adjacent to reception desk |
| REQ-08 | Support recurring bookings | Should Have | Front-desk staff | High-volume manual re-entry in current state |
| REQ-09 | Mobile-accessible interface | Should Have | Member feedback | Nice to have; not business-critical |
| REQ-10 | Utilisation reporting (rooms booked by day/time/type) | Could Have | Operations Manager | Deferred to Phase 2 |

---

## Solution Design

### Platform Decision Summary

| Criterion | Power Apps (proposed) | Custom React App (recommended) |
|---|---|---|
| Performance on client hardware | 8–12s load time | <2s target |
| Per-user licensing | $20–30 AUD/user/month | None (self-hosted) |
| UI flexibility | Constrained by canvas grid | Full control |
| Offline support | None | Partial (service worker caching) |
| Non-developer maintenance | Good (low-code editor) | Admin panel self-service |
| Azure migration path | Complex (platform lock-in) | Straightforward (containerise + App Service) |

REQ-06 — non-developer maintenance — was the strongest argument for Power Apps. This was addressed in the React build by implementing a self-service Admin Panel for all content changes (rooms, members, blocks), removing the need for developer involvement for day-to-day administration.

### Application Architecture — Local Deployment

```
┌─────────────────────────────────────────────┐
│              Client Network                  │
│                                             │
│  ┌─────────────┐      ┌──────────────────┐  │
│  │   React SPA  │◄────►│  Apache Server   │  │
│  │  (Browser)  │      │  (local host)    │  │
│  └─────────────┘      └────────┬─────────┘  │
│                                │             │
│                       ┌────────▼─────────┐  │
│                       │  JSON flat-file  │  │
│                       │   data store     │  │
│                       └──────────────────┘  │
└─────────────────────────────────────────────┘
```

**Why flat-file for Phase 1:** Booking volume did not justify a database server. A JSON flat-file store was sufficient and simplified the initial deployment. The schema was designed with a future SQL migration in mind — all IDs and relational references are structured as they would be in a normalised relational database.

### Front-End (React)

- Single-page application with React Router
- Three user roles rendered from the same codebase: Member view, Front-desk view, Admin view
- State managed via React Context
- CSS custom properties used for theming — high-contrast mode implemented as a CSS variable swap, toggled from the Admin Panel
- Key components: RoomGrid, BookingModal, AdminPanel, MyBookings, AvailabilityCalendar

### Screen Flow

```
Home (RoomGrid)
├── Room Detail → BookingModal → Confirmation
├── My Bookings → Cancel / Modify
└── Admin Panel (role-gated)
    ├── Room Management (add / edit / block)
    ├── Member Management
    └── Booking Overview + Display Settings (incl. high-contrast toggle)
```

### Data Schema (JSON — Phase 1)

Designed to map directly to a relational schema for Phase 2 SQL migration:

```json
{
  "rooms":       [{ "id", "name", "capacity", "floor", "active" }],
  "bookings":    [{ "id", "roomId", "memberId", "start", "end", "status", "recurringId" }],
  "members":     [{ "id", "name", "email", "company", "active" }],
  "adminBlocks": [{ "id", "roomId", "start", "end", "reason" }]
}
```

---

## Testing

| Test Type | Scope | Result |
|---|---|---|
| Performance benchmark | Time-to-interactive on front-desk tablet hardware | 1.4s average — target met ✓ |
| Overlap validation | Concurrent booking attempts on same room/time slot | Correctly rejected in all cases |
| Role-based rendering | Member / Front-desk / Admin views | All three roles render correct components; admin routes redirect unauthenticated users |
| High-contrast mode | Toggle via Admin Panel; render across all views | Pass — all UI elements readable in both modes |
| Recurring booking | Weekly pattern generator over 4-week test | Correct instances created; no duplicates |
| Admin block | Block room; verify member-facing availability updates | Pass |
| Usability (front-desk staff) | Task-based: "Book boardroom for Friday 2pm, 2 hours" | Completed in under 60 seconds by all 3 staff participants; 0 support queries in 2-week post-go-live period |

---

## Azure Migration Roadmap

The Phase 1 local deployment was designed as a stepping stone. The following migration architecture was scoped and documented for when the client is ready to move off on-premises infrastructure.

### Target Architecture

```
┌──────────────────────────────────────────────────────┐
│                 Azure (Australia East)                │
│                                                      │
│  ┌───────────────┐    ┌──────────────────────────┐  │
│  │ Azure App     │    │  Azure SQL Database       │  │
│  │ Service       │───►│  (migrated from JSON)     │  │
│  │ (React build) │    └──────────────────────────┘  │
│  └──────┬────────┘                                   │
│         │            ┌──────────────────────────┐   │
│         └───────────►│  Microsoft Entra ID       │   │
│                      │  (SSO, role assignment)   │   │
│                      └──────────────────────────┘   │
│                                                      │
│  ┌───────────────────────────────────────────────┐  │
│  │  Application Insights (telemetry + errors)    │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Migration Scope

| Component | Phase 1 (Current) | Phase 2 (Azure) | Notes |
|---|---|---|---|
| Hosting | Apache local server | Azure App Service (B1 tier) | React build deployed via GitHub Actions CI/CD |
| Data store | JSON flat-file | Azure SQL Database (Basic tier) | Schema already relational; migration script scoped |
| Authentication | Session-based (local) | Microsoft Entra ID (SSO) | Members and staff authenticate with existing M365 accounts |
| Monitoring | None | Application Insights | Error tracking, load time, usage telemetry |
| M365 integration | None | Microsoft Graph API | Calendar sync, Teams notifications on booking confirmation |
| Estimated monthly cost | $0 (on-premises) | ~$85–120 AUD/month | App Service B1 + SQL Basic + App Insights free tier |

### Migration Trigger Criteria

Agreed with the client as the conditions that would initiate the Azure migration:
- Booking volume exceeds 100/day (JSON flat-file performance threshold)
- Client expands to a second site (centralised hosting required)
- M365 calendar integration becomes a Must Have
- On-premises hardware approaches end-of-life

---

## Outcome

| Metric | Previous System | React App (post go-live) |
|---|---|---|
| Load time on front-desk tablet | Slow, inconsistent | 1.4 seconds average |
| Front-desk system bypass rate | High (staff defaulting to manual) | < 5% at 2-week review |
| Double bookings per week | ~3–4 (estimated) | 0 |
| Per-user licensing cost | N/A | $0 |
| Admin content changes requiring developer | Yes | No — Admin Panel self-service |
| Azure migration readiness | Not assessed | High — clean schema, containerisable |

---

## Reflections

The most consequential part of this engagement happened before any code was written. Accepting the CEO's Power Apps proposal without evaluation would have produced a solution that underperformed on the client's own hardware, introduced per-user licensing overhead, and created a platform dependency that would have complicated the eventual Azure migration. Running the evaluation first — and documenting the rationale — gave the recommendation credibility when it was presented.

REQ-06 (non-developer maintenance) was the strongest argument for Power Apps and the one I took most seriously. The Admin Panel in the React build was designed specifically to address it. If that requirement had been more complex — involving multi-table Dataverse relationships or deep Dynamics 365 integration — the platform decision might have gone the other way.

The flat-file-to-SQL schema design also mattered more than it seemed at the time. Designing data structures as if they will eventually live in a relational database, even when they don't yet, is a habit that consistently reduces migration risk later.

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant, Sydney NSW*
*[linkedin.com/in/arsh-wafiq-khan-chowdhury](https://linkedin.com/in/arsh-wafiq-khan-chowdhury)*
