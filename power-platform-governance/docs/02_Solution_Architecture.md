# 02 — Solution Architecture

**Client:** Ridgeline Partners  
**Author:** Arsh Wafiq Khan Chowdhury  
**Status:** Accepted  

---

## Purpose

This document defines how Ridgeline Partners' Power Platform solutions are structured, layered, and owned. It addresses the root cause of the timesheet outage — shared component ownership — and establishes the rules that prevent it from happening again.

---

## The Core Problem: Who Owns Shared Components?

The timesheet outage was caused by a canvas app solution that included a `Client Status` Dataverse table it did not build and did not own. When that solution was re-imported with a newer version of the table schema, it overwrote the shared version. Four other apps that depended on the original schema broke silently.

This is a solution ownership problem, not a deployment process problem. Better pipelines would not have prevented it — the import would have succeeded through any pipeline if the solution contained the conflicting component. The fix is architectural: shared components must live in a solution owned by the platform team, and application solutions must reference them rather than contain them.

---

## Solution Layers

Ridgeline's Power Platform estate is organised into two layers.

### Layer 1: Core (`RidgelineCore`)

The Core solution contains every component shared across two or more apps:

- All Dataverse tables (including `Client Status`, `Matter`, `Staff`, `Project`)
- Security roles
- Business units
- Environment variables and connection references
- Canvas component libraries
- Custom connectors (if any)

**Owner:** Platform team  
**Publisher:** `RidgelineCore` (prefix: `rco`)  
**Promotion:** Requires platform lead approval. Changes to Core block all App layer releases until Core is validated in Test and promoted to Production.

### Layer 2: App solutions (`RidgelineKM`, `RidgelineOps`, `RidgelineFinance`, etc.)

Each practice area or application has its own solution. App solutions contain:

- Canvas apps
- Power Automate flows
- Power BI reports (where embedded)
- App-specific tables (not shared with other apps)

App solutions **reference** Core components — they do not contain them. A canvas app in `RidgelineKM` that reads the `Client Status` table uses a connection reference defined in Core. If the Core table changes, that change is managed through the Core layer pipeline and all dependent apps receive it via Dataverse automatically.

**Owner:** Practice lead or designated maker  
**Publisher:** App-specific (e.g., `RidgelineKM`, prefix: `rkm`)  
**Promotion:** Follows the standard ring. Does not require platform lead approval unless it modifies or adds a shared component (which it should not).

---

## Publisher Strategy

Each solution has a distinct publisher. Publishers control the prefix applied to all component schema names.

| Solution | Publisher display name | Prefix |
|---|---|---|
| RidgelineCore | Ridgeline Core Platform | `rco_` |
| RidgelineKM | Ridgeline Knowledge Management | `rkm_` |
| RidgelineOps | Ridgeline Operations | `rops_` |
| RidgelineFinance | Ridgeline Finance | `rfin_` |

Using distinct prefixes makes it immediately visible — in Dataverse, in flow action names, in app formulas — which solution owns which component. It also prevents accidental naming collisions between layers.

**What was not chosen:** A single publisher for all solutions. This is common in smaller deployments and works until solutions are separated into layers, at which point all components share the same prefix and ownership becomes ambiguous. Establishing distinct publishers from the start is low-cost and avoids a painful migration later.

---

## Managed vs. Unmanaged Solutions

| Environment | Solution type |
|---|---|
| Development | Unmanaged |
| Test | Managed |
| Production | Managed |

Makers work with unmanaged solutions in Development. This allows direct editing of all components.

Managed solutions are imported into Test and Production. Managed solutions:

- Cannot be edited directly in the target environment
- Track the version from which they were imported
- Can be deleted cleanly without leaving orphan components
- Enforce layering — a managed Core solution cannot be overwritten by an App solution import

The pipeline (`release-solution.yml`) packs the unmanaged solution from source control into a managed solution before deploying to Test.

---

## Dependency Management

App solutions that depend on Core components must declare that dependency explicitly in the solution manifest. Power Platform will validate at import time that the required Core version is present in the target environment.

The order of deployment matters:

1. Deploy `RidgelineCore` to Test, validate, approve, deploy to Production
2. Deploy App solutions in any order (they depend on Core, not on each other)

The release pipeline enforces this order. The Core pipeline must complete before any App pipeline can be triggered against the same target environment. This is implemented via a GitHub Actions environment protection rule on the Test and Production deployment jobs.

---

## Source Control Structure

Solutions are stored in source control in unpacked form. The Power Platform CLI `pac solution unpack` command splits a `.zip` into individual files — one file per canvas app screen, one file per flow action, one file per Dataverse table schema.

```
solutions/
├── RidgelineCore/
│   ├── src/
│   │   ├── Entities/          ← Dataverse table definitions
│   │   ├── Roles/             ← Security role definitions
│   │   └── environmentvariabledefinitions/
│   └── Other/
│       └── Solution.xml       ← solution manifest
└── RidgelineKM/
    ├── src/
    │   ├── CanvasApps/        ← .msapp files (unpacked)
    │   └── Workflows/         ← flow definitions
    └── Other/
        └── Solution.xml
```

This structure means every pull request produces a readable diff. A reviewer can see that a new Dataverse column was added to the `Matter` table (`Entities/rco_matter.xml`) without needing to open a `.zip` file or import into an environment to inspect the change.

---

## Version Numbering

Solutions follow the pattern `Major.Minor.Patch.Build`:

- **Major** — breaking change to a shared interface (rare; requires coordinated release)
- **Minor** — new feature or component added
- **Patch** — bug fix or configuration change
- **Build** — auto-incremented by the release pipeline on every run

The release pipeline increments the Build number automatically. Minor and Patch are set by the developer in the solution manifest before raising a pull request. Major changes require platform lead review.
