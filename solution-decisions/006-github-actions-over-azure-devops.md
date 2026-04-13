# ADR 006 — GitHub Actions over Azure DevOps for Power Platform ALM

**Project:** Ridgeline Partners — Power Platform Governance & ALM Framework  
**Date:** 2026-03  
**Status:** Accepted  
**Author:** Arsh Wafiq Khan Chowdhury  

---

## Context

Ridgeline Partners needed an automated CI/CD pipeline to export, version, and deploy Power Platform solutions across a Development → Test → Production environment ring. Two tooling options are available within the Microsoft ecosystem: GitHub Actions with the `microsoft/powerplatform-actions` toolkit, and Azure DevOps Pipelines with the Power Platform Build Tools extension.

Both options are officially supported by Microsoft and capable of running the required workflows: export from Development, unpack to source, pack as managed, deploy to Test, approval gate, deploy to Production.

The decision needed to account for Ridgeline's existing tooling estate, team familiarity, and the overhead of introducing a new platform.

---

## Options Considered

### Option A: GitHub Actions with `microsoft/powerplatform-actions`

The official Microsoft Power Platform GitHub Actions toolkit provides individual actions for authentication (`who-am-i`), export, unpack, pack, import, publish, and Solution Checker. Workflows are defined in YAML files committed alongside solution source in the same repository.

**Advantages:**
- Single repository: source code, solution files, and pipeline definitions coexist in one place
- No additional platform license or subscription required — GitHub Free includes 2,000 minutes/month of Actions compute
- Familiar to the development team (Ridgeline uses GitHub for other technical projects)
- Pull request integration is native — the export pipeline commits directly to the PR branch and the diff is visible in the GitHub UI
- Open source — the action source is inspectable and forkable

**Disadvantages:**
- Less mature approval gate UI compared to Azure DevOps environments
- GitHub Actions secrets management is per-repository, not centralised across multiple repos (relevant at scale)
- Azure DevOps has a more sophisticated release pipeline model (stages, variable groups, deployment groups) that is better suited to very large programmes

### Option B: Azure DevOps Pipelines with Power Platform Build Tools

The Power Platform Build Tools extension is available from the Azure DevOps Marketplace and provides equivalent pipeline tasks to the GitHub Actions toolkit. Pipelines are defined in YAML (or via the classic visual editor) and run on Azure-hosted agents.

**Advantages:**
- Stronger approval and gate model — Azure DevOps pre-deployment approval gates support more complex governance workflows (multiple approvers, timeout policies, queries)
- Centralised variable groups — secrets and environment variables can be managed across multiple pipelines from a single location
- Better integration with Azure DevTest Labs and Azure Test Plans for organisations running formal testing programmes
- Native integration with Azure Boards for linking deployments to work items

**Disadvantages:**
- Requires an Azure DevOps organisation — Ridgeline does not currently have one, adding onboarding overhead
- Additional cost: Azure DevOps parallel pipeline minutes are not free beyond a basic allowance
- Splits the developer experience across two platforms (GitHub for source, Azure DevOps for pipelines)
- Steeper learning curve for makers who are unfamiliar with Azure DevOps

---

## Decision

**GitHub Actions with `microsoft/powerplatform-actions`.**

Ridgeline Partners does not have an existing Azure DevOps estate. Introducing Azure DevOps solely for Power Platform ALM would add an onboarding burden, split the developer experience across two platforms, and incur ongoing cost for a 15-maker team that does not need the advanced governance features Azure DevOps provides.

The GitHub Actions approach keeps all artefacts — solution source, unpacked components, and pipeline definitions — in a single repository. This makes the audit trail complete: every deployment is a commit, every commit is traceable to a pull request, and every pull request has a readable diff. The manual approval gate required before Production deployment is achievable via GitHub Environments with a required reviewer, which is sufficient for Ridgeline's governance requirements.

---

## Rationale

The governing factor is organisational fit, not technical capability. Both toolchains can run the same workflows against the same Power Platform environments using the same service principal authentication model. The difference is in the platform overhead and the developer experience.

For a firm of Ridgeline's size, the value of keeping things simple — one repository, one platform, a pipeline that a non-DevOps maker can read and understand — outweighs the advanced features that Azure DevOps provides. Those features become relevant when managing tens of environments, multiple teams, and a complex release calendar. Ridgeline is not there yet.

---

## Consequences

- All pipeline definitions are committed to the GitHub repository as `.yml` files in `pipelines/`
- GitHub repository secrets (`PP_APP_ID`, `PP_CLIENT_SECRET`, `PP_TENANT_ID`, `PP_DEV_URL`, `PP_TEST_URL`, `PP_PROD_URL`) must be maintained as the service principal or environment URLs change
- The Production deployment approval is configured via GitHub Environments → required reviewer. If Ridgeline's governance requirements evolve to require multiple approvers, timeout gates, or integration with Azure Boards work items, this decision should be revisited in favour of Azure DevOps
- If Ridgeline adopts Azure DevOps for other engineering work in future (e.g., .NET development, Azure infrastructure), this decision should be revisited to consolidate tooling

---

## References

- [microsoft/powerplatform-actions — GitHub](https://github.com/microsoft/powerplatform-actions)
- [Power Platform Build Tools for Azure DevOps — Microsoft Learn](https://learn.microsoft.com/en-us/power-platform/alm/devops-build-tools)
- [GitHub Environments — required reviewers](https://docs.github.com/en/actions/managing-workflow-runs/reviewing-deployments)
- [docs/05_ALM_Runbook.md](../power-platform-governance/docs/05_ALM_Runbook.md) — implementation runbook
