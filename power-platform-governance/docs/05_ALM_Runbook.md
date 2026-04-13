# 05 — ALM Runbook

**Client:** Ridgeline Partners  
**Author:** Arsh Wafiq Khan Chowdhury  
**Status:** Accepted  

---

## Purpose

This runbook defines the end-to-end developer workflow for Ridgeline Partners' Power Platform ALM pipeline — from making a change in Development through to a verified Production deployment. It also covers rollback procedures and the environment variable register.

This document is the day-to-day reference for makers and the platform lead. It assumes the environment ring and solution architecture described in `01_Environment_Strategy.md` and `02_Solution_Architecture.md` are in place.

---

## Prerequisites

Before any deployment can run, the following must be in place:

| Item | Where configured |
|---|---|
| Azure Entra ID service principal (`ridgeline-pp-pipeline`) | Azure Portal → Entra ID → App registrations |
| Service principal added as System Administrator in Dev, Test, and Prod | Power Platform Admin Centre → each environment → Security roles |
| GitHub secrets configured: `PP_APP_ID`, `PP_CLIENT_SECRET`, `PP_TENANT_ID`, `PP_DEV_URL`, `PP_TEST_URL`, `PP_PROD_URL` | GitHub repository → Settings → Secrets and variables → Actions |
| GitHub Environments configured: `test` (no protection rule), `production` (required reviewer: platform lead) | GitHub repository → Settings → Environments |
| `pac` CLI installed locally (optional, for manual validation) | `npm install -g @microsoft/powerplatform-actions` |

---

## Section 1: Making a Change (Developer Workflow)

### 1.1 — Set up the solution in Development

Ensure the solution you are modifying exists in the Development environment and is unmanaged. If starting a new solution:

1. Create the solution in the Development environment via Power Platform Admin Centre or the maker portal
2. Use the correct publisher (see `02_Solution_Architecture.md` for publisher prefixes)
3. Add all components into the solution — do not leave components unmanaged outside a solution

### 1.2 — Make and test changes in Development

Make all changes directly in the Development environment. Test the change manually:

- Canvas apps: open in preview mode, run through affected user journeys
- Flows: trigger manually and confirm run history shows success
- Dataverse changes: verify schema in the environment's table list

Coordinate with other makers working in the same environment. Check the `#pp-platform` Teams channel before modifying shared Core components.

### 1.3 — Create a feature branch

```bash
git checkout main
git pull
git checkout -b feature/[ticket-number]-[short-description]
# Example: feature/RP-42-add-matter-status-column
```

### 1.4 — Trigger the export pipeline

Push the branch to GitHub. Opening a pull request against `main` triggers the `export-solution.yml` pipeline automatically.

The export pipeline:
1. Authenticates to the Development environment using the service principal
2. Publishes all pending customisations (equivalent to "Publish all customisations" in the maker portal)
3. Exports the solution in unmanaged format
4. Unpacks the solution to source using `pac solution unpack`
5. Commits the unpacked source files to the feature branch
6. Posts a summary comment to the pull request

**If the export fails:** Check the Actions run log. Common causes are unpublished customisations (the pipeline publishes them, but if a canvas app has unsaved changes it will fail), or a service principal permission error if the principal has been removed from the environment's security roles.

### 1.5 — Review the pull request diff

After the export pipeline commits the unpacked source, review the diff in the pull request:

- **Dataverse table changes** appear in `solutions/[SolutionName]/src/Entities/`
- **Flow changes** appear in `solutions/[SolutionName]/src/Workflows/`
- **Canvas app changes** appear in `solutions/[SolutionName]/src/CanvasApps/`
- **Solution manifest version** should show an incremented version number in `Other/Solution.xml`

Request review from at least one other maker or the platform lead. Do not merge without an approval.

---

## Section 2: Releasing to Test and Production

### 2.1 — Merge to main

After pull request approval, merge the feature branch to `main`. This triggers `release-solution.yml`.

Do not squash merge — the commit history on `main` is the audit trail for what was deployed and when.

### 2.2 — Test deployment (automated)

The release pipeline runs automatically:

1. Packs the solution from source into a managed `.zip` using `pac solution pack`
2. Imports the managed solution into the Test environment
3. Runs Solution Checker against the import
4. Posts the result to the Actions run summary

Review the Solution Checker output. Warnings are acceptable. Critical violations must be resolved before the Production approval is granted — update the solution in Development, raise a new pull request, and re-run.

Manually validate in the Test environment:

- Open the app or trigger the flow as a test user
- Confirm the change behaves as expected against the Test environment's synthetic data
- Check for any broken connection references (these appear as warnings on flow runs)

### 2.3 — Production approval

The release pipeline pauses after the Test deployment and waits for a manual approval. The platform lead receives a GitHub Actions notification.

Before approving, the platform lead confirms:

- [ ] Test validation completed and signed off
- [ ] No critical Solution Checker violations
- [ ] Environment variable values for Production are correct (see Section 4)
- [ ] Deployment is not scheduled during a blackout window (month-end billing close, client deliverable dates)

Approve the deployment in the GitHub Actions interface. Rejecting the approval cancels the Production deployment — the Test import remains in place and can be redeployed after the blocking issue is resolved.

### 2.4 — Production deployment (automated)

On approval, the pipeline imports the same managed solution `.zip` to Production. The import uses the same service principal credentials.

Post-deployment: open the Production environment and confirm the change is visible and functional. Check the maker portal for any suspended flows — a suspended flow indicates a DLP violation or a missing connection that was not caught in Test.

---

## Section 3: Rollback Procedure

Power Platform managed solutions support rollback by reinstating a previous version.

### 3.1 — Identify the last known good version

Check the GitHub Actions run history for the most recent successful Production deployment. Note the commit SHA and the solution version number from the `Solution.xml` in that commit.

Alternatively, check the solution history in Power Platform Admin Centre → Production environment → Solutions → [Solution name] → History.

### 3.2 — Roll back via pipeline (preferred)

Revert the merge commit on `main`:

```bash
git revert [merge-commit-sha]
git push origin main
```

This triggers the release pipeline with the reverted source. The pipeline will pack and deploy the previous version as a new managed solution import, overwriting the problematic version.

### 3.3 — Roll back manually (emergency)

If the pipeline cannot run (service principal issue, GitHub outage), the platform lead can manually import the previous managed solution `.zip` from the GitHub Actions artefacts. Each release pipeline run uploads the packed solution as a workflow artefact retained for 30 days.

1. Download the artefact from the previous successful Actions run
2. Import via Power Platform Admin Centre → Production → Solutions → Import
3. Document the manual import in the Teams `#pp-platform` channel with the reason and solution version

After a manual rollback, the pipeline must be verified to be functioning correctly before the next release proceeds.

---

## Section 4: Environment Variable Register

All environment variables and connection references used in Ridgeline solutions are registered here. Update this register whenever a new variable is added to any solution.

| Display name | Schema name | Solution | Dev value | Test value | Prod value | Owner |
|---|---|---|---|---|---|---|
| SharePoint Site URL | `rco_SharePointSiteUrl` | RidgelineCore | `https://ridgeline-dev.sharepoint.com/sites/platform` | `https://ridgeline-test.sharepoint.com/sites/platform` | `https://ridgeline.sharepoint.com/sites/platform` | Platform lead |
| AI Endpoint | `rco_AzureOpenAIEndpoint` | RidgelineCore | `https://ridgeline-dev-openai.openai.azure.com/` | `https://ridgeline-test-openai.openai.azure.com/` | `https://ridgeline-openai.openai.azure.com/` | Platform lead |
| Notification Email | `rko_NotificationEmail` | RidgelineOps | `pp-test@ridgeline.com.au` | `pp-test@ridgeline.com.au` | `pp-platform@ridgeline.com.au` | Platform lead |

Connection references are configured in the target environment by the platform lead after each new solution import. They are not included in the managed solution because connection credentials differ by environment.

---

## Section 5: Deployment Blackout Windows

Deployments to Production are not permitted during:

- Last business day of each calendar month (billing close)
- During active client deliverable periods (communicated by the Head of Digital at least 48 hours in advance)
- Public holidays

Deployments targeting a post-blackout window should be queued in the `#pp-platform` Teams channel and released on the first permitted business day.
