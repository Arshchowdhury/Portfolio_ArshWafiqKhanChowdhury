# 01 — Environment Strategy

**Client:** Ridgeline Partners  
**Author:** Arsh Wafiq Khan Chowdhury  
**Status:** Accepted  

---

## Purpose

This document defines the Power Platform environment ring for Ridgeline Partners — the number of environments, their purpose, what is permitted in each, and the criteria that trigger promotion from one to the next.

Environment design is one of the first conversations in any Power Platform governance engagement because getting it wrong is expensive to fix. Adding a test environment after a year of production-only deployments requires migrating data, re-establishing connections, and rebuilding maker habits. It is better to define the model at the start and size it appropriately for the organisation.

---

## Environment Ring

Ridgeline Partners will operate three environments plus a sandbox allocation for experimentation.

```
Sandbox (per maker, on request)
        │
        ▼
Development (shared, team-accessible)
        │
        ▼
Test (Managed Environment — automated deployment via pipeline)
        │
        ▼
Production (Managed Environment — manual approval gate)
```

### Development

| Property | Value |
|---|---|
| Purpose | Active development, integration, peer review |
| URL | `ridgeline-dev.crm6.dynamics.com` |
| Type | Standard environment |
| Managed Environment | No |
| Data | Synthetic test data only — no client data |
| Access | All licensed makers, read/write |
| Deployment method | Manual (makers work directly) |
| Region | Australia East |

Development is intentionally ungoverned. Makers iterate quickly here without pipeline friction. The governance boundary is at promotion — not at creation.

A single shared Development environment is appropriate for Ridgeline's team size (15 makers). At larger scale, each team or workstream would receive its own Development environment to avoid cross-team conflicts on shared components.

### Test

| Property | Value |
|---|---|
| Purpose | Validate managed solutions before Production release |
| URL | `ridgeline-test.crm6.dynamics.com` |
| Type | Managed Environment |
| Managed Environment | Yes |
| Data | Synthetic data mirroring Production schema |
| Access | Platform team (read/write), makers (read only) |
| Deployment method | Automated via `release-solution.yml` pipeline |
| Region | Australia East |

Test receives managed solution imports only — no direct editing. Any change to Test must go through the pipeline. This enforces the rule that Production will only ever see what Test has validated.

Managed Environments is enabled on Test to enforce the DLP policy, activate the Solution Checker on import, and generate the weekly admin digest.

### Production

| Property | Value |
|---|---|
| Purpose | Live business operations |
| URL | `ridgeline.crm6.dynamics.com` |
| Type | Managed Environment |
| Managed Environment | Yes |
| Data | Live client and operational data |
| Access | End users (run only), platform team (read/write for support) |
| Deployment method | Automated via pipeline with manual approval gate |
| Region | Australia East |

No maker has direct edit access to Production. All changes arrive as managed solution imports through the pipeline. The manual approval gate before the Production deployment step requires sign-off from the platform lead.

### Sandbox (per request)

| Property | Value |
|---|---|
| Purpose | Proof-of-concept, personal experimentation, training |
| URL | `ridgeline-sandbox-[firstname].crm6.dynamics.com` |
| Type | Trial or Developer environment |
| Managed Environment | No |
| Data | None — maker's own synthetic data |
| Access | Requesting maker only |
| Lifecycle | 30 days, renewable on request |

Sandboxes are provisioned on request via the maker onboarding flow (see `04_Maker_Access_Model.md`). They are isolated from all other environments and cannot be promoted into the ring directly — work must be exported from the sandbox and imported to Development to enter the pipeline.

---

## Environment Naming Convention

All environments follow the pattern: `[ClientShortName]-[ring]`

| Environment | Display name | URL |
|---|---|---|
| Development | Ridgeline - Development | `ridgeline-dev.crm6.dynamics.com` |
| Test | Ridgeline - Test | `ridgeline-test.crm6.dynamics.com` |
| Production | Ridgeline | `ridgeline.crm6.dynamics.com` |
| Sandbox | Ridgeline - Sandbox - [Name] | `ridgeline-sandbox-[name].crm6.dynamics.com` |

Consistent naming makes the environment list readable in the Power Platform Admin Centre and reduces the risk of a maker accidentally deploying to the wrong target.

---

## Promotion Criteria

A solution component may be promoted from Development to Test when:

- The change is committed to a feature branch in the GitHub repository
- A pull request has been raised, reviewed, and approved by at least one other maker or the platform lead
- The export pipeline has run successfully and the unpacked source is committed
- No conflicts exist with components owned by the Core solution layer

A solution may be deployed to Production when:

- The managed solution import to Test has completed without errors
- The Solution Checker report contains no critical violations
- Manual validation in Test has been signed off by the platform lead
- A production deployment approval has been granted in the GitHub Actions workflow

---

## Environment Variable Strategy

Connection references and environment variables must be defined in the solution and configured separately in each environment. This is a Power Platform requirement for managed solutions and is a frequent source of deployment failures when not planned for.

For each connection reference and environment variable in Ridgeline's solutions, the following is documented:

- The display name and schema name
- The value in Development (synthetic endpoint or test credential)
- The value in Test
- The value in Production
- Who is responsible for updating the value when it changes

This register is maintained in `docs/05_ALM_Runbook.md`, section 4.

---

## What Was Not Chosen

**A single environment with security roles** — some organisations manage access by creating security roles within a single production environment and restricting what makers can see. This provides access separation but no deployment isolation. A bad import in this model still affects live users. Rejected.

**Azure DevOps instead of GitHub** — see `solution-decisions/006-github-actions-over-azure-devops.md`.

**Four-environment ring (Dev → SIT → UAT → Prod)** — appropriate for regulated industries or large enterprise programmes. For a 220-person firm with 15 makers, four environments introduce overhead that is disproportionate to the risk. Three environments provides the essential separation: a place to build, a place to validate, and a place to run.
