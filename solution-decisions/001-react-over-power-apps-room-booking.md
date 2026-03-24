# ADR 001 — React over Power Apps for Room Booking System

**Status:** Accepted
**Date:** March 2026
**Context:** Room booking system replacement for a Sydney co-working operator

---

## Context

The organisation had an existing web-based room booking system that was outdated and staff were bypassing it. The CEO proposed rebuilding the system on Microsoft Power Apps, citing existing Microsoft 365 licences and the low-code appeal for non-developer maintenance.

Before committing to a build, a structured platform evaluation was conducted against the client's specific requirements and constraints.

---

## Decision

Build a custom React single-page application hosted on the client's existing Apache server, rather than rebuilding on Power Apps.

---

## Options Considered

**Option 1: Power Apps canvas app (proposed)**
- Pros: Low-code, easy for non-developers to modify, native M365 integration, quick to scaffold
- Cons: Canvas app runtime load time averaged 8–12 seconds on client hardware; per-user licensing cost for casual users; constrained UI for specific UX requirements (high-contrast mode, minimal-tap workflows); no offline support; creates platform lock-in that complicates Azure migration

**Option 2: Custom React SPA on Apache (chosen)**
- Pros: <2s load time on existing hardware; no per-user licensing; full UI flexibility; offline support via service worker; clean path to Azure App Service
- Cons: Requires developer for structural changes; higher initial build effort

**Option 3: Third-party SaaS booking tool**
- Pros: Low setup effort; feature-complete out of the box
- Cons: Per-user subscription cost; no customisation; vendor dependency; no migration path to internal infrastructure

---

## Rationale

REQ-01 (performance) and REQ-02 (licensing cost) were hard blockers for Power Apps in this context. The per-user licensing model adds significant cost at scale for a system used by casual members and part-time staff. The load time issue was a front-desk workflow problem, not a minor inconvenience.

The strongest argument for Power Apps was REQ-06 (non-developer maintenance). This was addressed in the React build by implementing a self-service Admin Panel that handles all content changes (rooms, members, blocks, display settings) without requiring code changes.

Power Apps remains appropriate for this client's use case if the requirements shift: if they add Dynamics 365, if all users hold M365 licences, or if a model-driven app backed by Dataverse is needed. The decision was requirements-driven, not preference-driven.

---

## Consequences

- React app deployed on Apache; load time <2s confirmed in testing
- Admin Panel covers all day-to-day content changes without developer involvement (REQ-06 met)
- JSON flat-file data store used for Phase 1 (see ADR-002); schema designed for SQL migration
- Azure migration roadmap documented; containerisation straightforward from this codebase
- Power Apps competency demonstrated through the evaluation, not the build

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant*
