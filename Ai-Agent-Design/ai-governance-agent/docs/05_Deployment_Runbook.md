# Deployment Runbook
**AI Governance Advisory Agent**
Meridian Advisory Group | Phase 5 of 5

---

## Purpose

This runbook defines the step-by-step procedure for deploying the AI Governance Advisory Agent from the Test environment to Production. It is intended for IT Operations staff performing the deployment. The delivery team is available during the deployment window for support.

Estimated deployment duration: 3 to 4 hours including verification.

**Prerequisites:**
- UAT sign-off obtained (document 04_UAT_Test_Cases.md)
- CRO approval confirmed in writing
- Deployment window booked (recommended: Saturday 08:00 to 12:00 AEST)
- IT Operations lead and a nominated delivery team contact on a Teams call throughout

---

## Environment Overview

| Environment | URL / Location | Purpose |
|---|---|---|
| Development | Dev Power Platform environment | Build and active development |
| Test | Test Power Platform environment | UAT and pre-release validation |
| Production | Production Power Platform environment | Live service |

The Default Power Platform environment is not used.

---

## Pre-Deployment Checklist

Complete all items before beginning deployment. Do not proceed if any item is not confirmed.

| # | Check | Owner | Status |
|---|---|---|---|
| 1 | UAT sign-off document signed by CRO and Head of AI Practice | Delivery team | Confirm |
| 2 | Azure AI Search Standard tier resource provisioned in Australia East | IT Operations | Confirm |
| 3 | Production SharePoint site and document library created (AI-Governance-KB) | IT Operations | Confirm |
| 4 | Production SharePoint Audit List created with correct column schema | IT Operations | Confirm |
| 5 | Production Power Platform environment created (not Default) | IT Operations | Confirm |
| 6 | AAD groups created: AI-Governance-KnowledgeWorkers, AI-Governance-RiskTeam, AI-Governance-Admins | IT Operations | Confirm |
| 7 | Power BI workspace created and permission groups assigned | IT Operations | Confirm |
| 8 | Service principal created for Power Automate SharePoint connection | IT Operations | Confirm |
| 9 | Knowledge base documents uploaded to Production SharePoint library (reviewed and approved versions) | AI Practice | Confirm |
| 10 | Rollback plan reviewed and rollback contacts confirmed | IT Operations | Confirm |

---

## Step 1: Azure AI Search Configuration

**Estimated time: 45 minutes**

### 1.1 Create the search index

1. Open the Azure portal and navigate to the AI Search resource provisioned for Production (Australia East region).
2. Select **Indexes** from the left menu and select **Add index**.
3. Name the index `meridian-ai-governance`.
4. Add the following fields to the index schema:

| Field name | Type | Attributes |
|---|---|---|
| id | Edm.String | Key, Retrievable |
| title | Edm.String | Retrievable, Searchable |
| content | Edm.String | Retrievable, Searchable |
| sourceUrl | Edm.String | Retrievable |
| lastModified | Edm.DateTimeOffset | Retrievable, Filterable, Sortable |
| author | Edm.String | Retrievable |

5. Save the index.

### 1.2 Configure semantic search

1. In the index settings, select **Semantic configurations**.
2. Add a new configuration named `semantic-config`.
3. Set the title field to `title` and content fields to `content`.
4. Save the configuration.

### 1.3 Create the SharePoint indexer

1. Select **Data sources** and add a new source of type **SharePoint Online**.
2. Provide the Production SharePoint site URL and document library path `AI-Governance-KB`.
3. Authenticate using the service principal created in the pre-deployment checklist.
4. Create an indexer named `meridian-kb-indexer` targeting the `meridian-ai-governance` index.
5. Set the schedule to **Daily at 02:00 AEST**.
6. Run the indexer once manually and confirm it completes without error.
7. Verify document count in the index matches the number of documents in the SharePoint library.

**Verification:** In the Azure portal, select the index and choose **Search explorer**. Run a query for `"AI Act"` and confirm results are returned.

---

## Step 2: SharePoint Configuration

**Estimated time: 30 minutes**

### 2.1 Confirm knowledge base library permissions

1. Navigate to the Production SharePoint site.
2. Open the `AI-Governance-KB` document library settings.
3. Confirm permissions:
   - `AI-Governance-KnowledgeWorkers` AAD group: Read
   - `AI-Governance-Admins` AAD group: Contribute
4. Break permission inheritance from the site if required so that library permissions are managed independently.

### 2.2 Verify audit list schema

1. Open the SharePoint Audit List (list name: `AI-Governance-Audit`).
2. Confirm the following columns exist with the correct types:

| Column name | Type |
|---|---|
| SessionID | Single line of text |
| UserUPN | Single line of text |
| Timestamp | Date and time |
| QueryText | Multiple lines of text |
| ResponseSummary | Multiple lines of text |
| SourceDocuments | Multiple lines of text |
| ConfidenceBand | Choice (High, Medium, Escalated) |
| EscalatedTo | Single line of text |
| EnvironmentName | Single line of text |

3. Confirm that Timestamp and UserUPN columns are indexed (for performance on large list views).
4. Confirm list permissions: `AI-Governance-RiskTeam` and `AI-Governance-Admins` have Read access. All other groups have no access.

---

## Step 3: Power Automate Deployment

**Estimated time: 30 minutes**

### 3.1 Export flow from Test environment

1. In the Test Power Platform environment, open the **AI-Governance-AuditFlow** solution.
2. Select **Export** and choose **Managed solution**.
3. Download the solution .zip file.

### 3.2 Import flow to Production environment

1. Navigate to the Production Power Platform environment.
2. Select **Solutions** and then **Import solution**.
3. Upload the managed solution .zip file exported from Test.
4. During import, when prompted for connection references, create new connections using the Production service principal:
   - SharePoint connection: authenticate with the service principal, confirm Production SharePoint site URL
   - Teams connection: authenticate with the service principal account used for Teams notifications
5. Complete the import.

### 3.3 Verify flow is active

1. Open the imported solution and select the **AI-Governance-AuditFlow** cloud flow.
2. Confirm the flow status is **On**.
3. Copy the HTTP trigger URL. This will be provided to the Copilot Studio deployment in Step 4.
4. Send a test HTTP POST to the trigger URL with a sample payload (template below) and confirm a record is written to the Production audit list.

**Sample test payload:**
```json
{
  "sessionId": "TEST-001",
  "userUPN": "deploymenttest@meridian.com.au",
  "queryText": "Deployment verification test query",
  "responseSummary": "This is a test record created during deployment verification",
  "sourceDocuments": "EU_AI_Act_FullText_April2024.pdf",
  "confidenceBand": "High",
  "escalatedTo": "",
  "environmentName": "Production"
}
```

**Verification:** Confirm the test record appears in the SharePoint Audit List. Note the record ID and confirm all fields are populated correctly. Delete the test record after verification.

---

## Step 4: Copilot Studio Deployment

**Estimated time: 60 minutes**

### 4.1 Export agent from Test environment

1. In the Test Power Platform environment, open the **AI-Governance-Agent** solution.
2. Select **Export** and choose **Managed solution**.
3. Download the solution .zip file.

### 4.2 Import agent to Production environment

1. Navigate to the Production Power Platform environment.
2. Select **Solutions** and then **Import solution**.
3. Upload the managed solution .zip file.
4. During import, update the following environment variables to Production values:

| Variable name | Production value |
|---|---|
| AuditFlowURL | HTTP trigger URL from Step 3.3 |
| SearchEndpoint | Production Azure AI Search endpoint URL |
| SearchIndexName | meridian-ai-governance |
| SearchAPIKey | Production API key from Azure AI Search resource |
| EscalationContactUPN | daniel.soh@meridian.com.au |

5. Complete the import.

### 4.3 Publish the agent

1. Open the imported Copilot Studio agent in the Production environment.
2. Review all topics to confirm they imported correctly (expected: 5 topics as documented in the SDD).
3. Select **Publish** from the top navigation.
4. Wait for the publish operation to complete (typically 2 to 5 minutes).

### 4.4 Configure the Teams channel

1. In Copilot Studio, select **Channels** from the left navigation.
2. Select **Microsoft Teams**.
3. Select **Turn on Teams** and follow the authentication prompts.
4. Once enabled, open the Teams admin centre and navigate to **Teams apps** and then **Manage apps**.
5. Locate the agent and set availability to the `AI-Governance-KnowledgeWorkers` AAD group.
6. Allow up to 24 hours for the app to appear in Teams for assigned users (Microsoft propagation time).

**Verification:** Using a test account in the `AI-Governance-KnowledgeWorkers` group, open Microsoft Teams and navigate to Apps. Search for the agent by name. Confirm it is available and can be installed.

---

## Step 5: Power BI Dashboard Deployment

**Estimated time: 30 minutes**

### 5.1 Publish the report to the Production workspace

1. Open the Power BI Desktop file (`AI-Governance-Compliance-Dashboard.pbix`) on the deployment workstation.
2. Update the data source connection to point to the Production SharePoint Audit List URL.
3. Select **Home** then **Publish** and select the Production Power BI workspace.

### 5.2 Configure scheduled refresh

1. In the Power BI Service, navigate to the Production workspace.
2. Open the dataset settings for the published report.
3. Under **Scheduled refresh**, enable refresh and set the schedule to every 4 hours during business hours (06:00 to 20:00 AEST, Monday to Friday).
4. Configure the gateway connection using the SharePoint connector and service principal credentials.

### 5.3 Share the dashboard

1. In the Production workspace, open the dashboard.
2. Select **Share** and add the `AI-Governance-RiskTeam` AAD group with Viewer permissions.
3. Add the `AI-Governance-Admins` group with Viewer permissions.
4. Do not enable the **Allow recipients to share** option.

**Verification:** Log in to Power BI Service with a test account in the `AI-Governance-RiskTeam` group. Confirm the dashboard is accessible and loads without error.

---

## Step 6: Post-Deployment Verification

**Estimated time: 30 minutes**

Complete all verification steps before declaring the deployment successful.

| # | Verification step | Expected outcome | Result |
|---|---|---|---|
| V-001 | Submit an in-scope query via Teams using a production user account | Response returned within 10 seconds with citation | |
| V-002 | Submit an out-of-scope query | Agent escalates and sends Teams notification to Daniel Soh | |
| V-003 | Review SharePoint Audit List after V-001 and V-002 | Two audit records present with all fields populated, EnvironmentName = Production | |
| V-004 | Trigger a Power BI refresh manually | Dashboard updates and shows the two V-001/V-002 test records | |
| V-005 | Attempt to access Audit List as a general staff account | Access denied (SharePoint permission error) | |
| V-006 | Confirm AI Search index has the correct document count | Count matches number of documents in SharePoint KB library | |

Sign each verification step off before proceeding.

---

## Rollback Procedure

If a critical failure occurs during deployment, follow this procedure:

1. Stop all deployment activities immediately.
2. Notify the CRO and Head of AI Practice of the rollback.
3. In the Production Power Platform environment, uninstall any managed solutions imported during this deployment.
4. Confirm the Test environment agent remains intact (it should be unaffected by Production deployment).
5. Delete any Production SharePoint records created during failed verification steps.
6. Document the failure, capture error logs, and schedule a remediation session with the delivery team.

The Test environment agent remains operational and can be used by nominated staff as a temporary fallback if agreed by the CRO.

---

## Support Contacts

| Role | Name | Contact |
|---|---|---|
| IT Operations lead | On-call IT Operations | Teams: IT-Ops channel |
| Delivery team contact | Arsh Chowdhury | Direct Teams message |
| Head of AI Practice | Daniel Soh | Direct Teams message |
| Azure support | Microsoft | Azure portal support case |

---

## Go-Live Sign-Off

| Name | Role | Signature | Date |
|---|---|---|---|
| IT Operations Lead | Infrastructure | | Week 8 |
| Head of AI Practice | Business owner | | Week 8 |
| Chief Risk Officer | Executive sponsor | | Week 8 |

---

*Document version 1.0. Prepared by Arsh Chowdhury, Technology Consultant. Simulated engagement for portfolio purposes.*
