# Power Platform Governance & ALM Framework

**Client:** Ridgeline Partners (simulated) — 220-person management consultancy, Sydney  
**Engagement type:** Platform governance and DevOps implementation  
**Delivery phase:** Discovery → Design → Implementation → Handover  

---

## Business Problem

Ridgeline Partners had a maker culture that worked — until it didn't.

Over two years, fifteen Power Platform makers across four practice groups had built canvas apps, Power Automate flows, and Dataverse tables that saved the firm an estimated $180K in third-party tooling costs. All of it lived in a single production environment. Solutions were deployed by downloading `.zip` files and importing them manually. There was no test environment, no version control, and no record of what had been changed by whom.

Three weeks before this engagement started, a maker in the Finance practice exported a solution containing a shared `Client Status` component. The import overwrote the version that four other apps depended on. The firm's timesheet application — used by all 220 staff on the last business day of the billing month — was down for six hours. The COO escalated. The CTO wanted a pipeline. The Head of Digital didn't want to kill the culture that had saved the firm money.

The brief: design and implement a governance framework that makes deployments safe, traceable, and recoverable — without turning every change into a change-control ticket.

---

## Solution Overview

A three-environment ring (Development → Test → Production) with automated export and release pipelines via GitHub Actions, Managed Environments on Test and Production, a DLP connector policy enforcing connector tiering, and Entra ID security groups governing maker access.

The framework separates the firm's Power Platform estate into two solution layers:

- **Core layer** (`RidgelineCore`) — shared components: Dataverse tables, security roles, environment variables, connection references. Owned by the platform team. Promoted through the full ring.
- **App layer** (`RidgelineKM`, `RidgelineOps`, etc.) — practice-specific apps and flows. Each has its own solution, its own pipeline, and can be released independently without touching Core.

This layering was the most important architectural decision in the engagement. The timesheet outage happened because a practice-level solution owned a shared component it had no business owning. Separating ownership at the solution layer prevents that class of error structurally.

---

## Delivery Structure

| Phase | Document | Summary |
|---|---|---|
| Discovery | [Environment Strategy](docs/01_Environment_Strategy.md) | Ring model, environment purposes, naming, promotion criteria |
| Design | [Solution Architecture](docs/02_Solution_Architecture.md) | Solution layering, publisher strategy, dependency management |
| Design | [DLP Policy Design](docs/03_DLP_Policy_Design.md) | Connector tiering rationale, business/non-business/blocked |
| Design | [Maker Access Model](docs/04_Maker_Access_Model.md) | Entra groups, license assignment, onboarding workflow |
| Implementation | [ALM Runbook](docs/05_ALM_Runbook.md) | Developer workflow, release process, rollback procedure |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Platform | Microsoft Power Platform (Power Apps, Power Automate, Dataverse) |
| Environments | Power Platform Managed Environments |
| Governance | Power Platform DLP policies, Tenant isolation |
| Identity | Azure Entra ID security groups, service principal |
| CI/CD | GitHub Actions, `microsoft/powerplatform-actions` toolkit |
| Infrastructure | PowerShell + Power Platform CLI (`pac`) |
| Source control | GitHub (solution unpacked to source — not `.zip`) |

---

## Pipeline Architecture

```
Developer (Dev environment)
    │
    │  makes changes, commits to feature branch
    ▼
GitHub (Pull Request)
    │
    ├── export-solution.yml triggers
    │       exports solution from Dev
    │       unpacks to source (readable diff)
    │       commits unpacked source to branch
    ▼
GitHub (Merge to main)
    │
    ├── release-solution.yml triggers
    │       packs managed solution from source
    │       imports to Test environment
    │       runs automated validation
    │       waits for manual approval gate
    │       imports to Production environment
    ▼
Production (Managed Environment)
```

All deployments use a service principal — no human credentials in the pipeline.

---

## Key Design Decisions

**Solution layering over monolithic deployment** — see [ADR 006](../solution-decisions/006-github-actions-over-azure-devops.md) for the GitHub Actions vs Azure DevOps decision, and `docs/02_Solution_Architecture.md` for the layering rationale.

**Managed Environments on Test and Production only** — Development is intentionally ungoverned to preserve maker speed. The guardrails engage at the point of promotion, not during creation.

**Unpack solutions to source control** — `.zip` files are binary and produce meaningless diffs. Unpacking means every component (canvas app screen, flow action, Dataverse schema) is a readable file. A reviewer can see exactly what changed before approving a pull request.

**Manual approval gate before Production** — automated deployment to Test, human decision before Production. This matches the governance appetite of a 220-person firm that is not running a continuous deployment model.

---

## Files in This Repository

```
power-platform-governance/
├── README.md                          ← this file
├── docs/
│   ├── 01_Environment_Strategy.md     ← ring model and environment design
│   ├── 02_Solution_Architecture.md    ← solution layering and publisher strategy
│   ├── 03_DLP_Policy_Design.md        ← connector tiering and policy rationale
│   ├── 04_Maker_Access_Model.md       ← Entra groups and maker onboarding
│   └── 05_ALM_Runbook.md             ← step-by-step developer and release workflow
├── pipelines/
│   ├── export-solution.yml            ← GitHub Actions: export and unpack from Dev
│   └── release-solution.yml          ← GitHub Actions: pack, deploy Test, approve, deploy Prod
└── scripts/
    └── validate-environment.ps1      ← PowerShell pre-flight checks before deployment
```

The sixth Architecture Decision Record for this engagement — GitHub Actions over Azure DevOps — lives in the repository's root [`solution-decisions/`](../solution-decisions/) folder alongside the decisions from other engagements.

---

## Outcomes

| Metric | Before | After |
|---|---|---|
| Deployment method | Manual `.zip` import | Automated pipeline with audit trail |
| Test environment | None | Managed Environment with DLP enforced |
| Change visibility | None | Full diff on every pull request |
| Rollback capability | Manual re-import of old file (if saved) | Git revert → pipeline re-run |
| Maker onboarding | Ad hoc | Entra group request → automated license assignment |
| Time to deploy (simple change) | ~25 min (export, import, test manually) | ~8 min (commit, pipeline, auto-validation) |
| Outage risk from shared component conflict | Unmitigated | Eliminated by solution layering |

---

## What Would Change for a Larger Enterprise

This framework is sized for a 220-person firm with 15 makers and a small platform team. For a 2,000-person enterprise the following would change:

- **CoE Starter Kit** — the Microsoft Centre of Excellence toolkit would be deployed to provide tenant-wide inventory, compliance scoring, and maker request flows via a model-driven app rather than manual Entra group requests.
- **Azure DevOps Pipelines over GitHub Actions** — for firms with an existing Azure DevOps estate, the `microsoft/powerplatform-actions` equivalents in the ADO extension pack would be used instead. The pipeline logic is identical; the tooling differs.
- **Environment-per-team** — at scale, each team or workstream gets its own Dev environment rather than sharing a single Dev. Promotion still flows through a shared Test and Production ring.
- **Automated testing** — Power Apps Test Studio tests and flow run assertions would be incorporated into the Test stage before the approval gate, rather than relying solely on manual validation.
