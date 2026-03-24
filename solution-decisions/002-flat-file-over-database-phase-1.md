# ADR 002 — JSON Flat-File over Database for Phase 1 Deployment

**Status:** Accepted
**Date:** March 2026
**Context:** Room booking system - data storage decision for local server deployment

---

## Context

Having decided to build a React SPA on the client's Nginx server (see ADR-001), a data storage approach was needed for Phase 1. The system needed to store rooms, bookings, members, and admin blocks. The client had no existing database server. Setting one up would add infrastructure complexity, a maintenance burden, and cost.

---

## Decision

Use a JSON flat-file store for Phase 1, with the schema explicitly designed to map to a relational database for Phase 2 migration.

---

## Options Considered

**Option 1: JSON flat-file (chosen)**
- Pros: Zero infrastructure overhead; no setup required; sufficient for Phase 1 booking volume; simplifies deployment; easy backup (a file copy)
- Cons: No concurrent write safety at scale; performance degrades beyond ~500 records per entity; no query language; no access control at the data layer

**Option 2: SQLite**
- Pros: Relational queries; lightweight; no server required; good for low-traffic use
- Cons: File-locking issues with concurrent writes in a web context; not trivially migrated to a managed Azure SQL instance

**Option 3: MySQL/PostgreSQL on local server**
- Pros: Full relational capabilities; concurrent write safety; straightforward Azure migration
- Cons: Additional infrastructure to maintain; requires database administration the client cannot perform; overkill for Phase 1 volume

---

## Rationale

Booking volume for Phase 1 was under 50 bookings per day across one site. A JSON flat-file is entirely sufficient at this volume and removes all database infrastructure overhead from a client who has no IT administrator.

The critical design constraint was that the Phase 2 migration risk needed to be low. This was addressed by structuring the JSON schema as if it were a normalised relational database - all entities have explicit IDs, foreign key relationships use ID references rather than embedded objects, and the schema maps directly to a four-table SQL design (rooms, bookings, members, adminBlocks). The migration script to Azure SQL was scoped as part of the Phase 2 roadmap.

---

## Consequences

- No database infrastructure required for Phase 1
- Backup is a file copy; operations staff can perform it without training
- Phase 2 migration to Azure SQL is a defined, low-risk task rather than a schema redesign
- Performance threshold for Phase 2 trigger: 100 bookings/day or second-site expansion

---

*Arsh Wafiq Khan Chowdhury — Technology Consultant*
