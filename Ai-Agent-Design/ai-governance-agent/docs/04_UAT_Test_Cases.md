# User Acceptance Testing
**AI Governance Advisory Agent**
Meridian Advisory Group | Phase 4 of 5

---

## Test Approach

UAT was conducted over two weeks (Weeks 6 and 7 of the engagement) in the Test environment. Fifteen business users participated across Legal, Risk, and Strategy practices. Test cases were executed by testers against defined acceptance criteria. Results were reviewed with the CRO and Head of AI Practice before sign-off.

**Environment:** Test (pre-production)
**Data:** Anonymised production-like knowledge base content
**Access:** 15 nominated UAT participants, IT Operations (observer), Delivery team (support)
**Tools:** Microsoft Teams (agent channel), SharePoint Audit List (direct review), Power BI Test workspace

---

## Test Scope

| Area | In scope | Out of scope |
|---|---|---|
| Agent responses | Yes | Agent source code or flow internals |
| Citation accuracy | Yes | Document authoring or content accuracy |
| Escalation pathway | Yes | SME response quality |
| Audit log completeness | Yes | Log retention (tested in production) |
| Power BI dashboard | Yes | Power BI licensing configuration |
| Performance | Yes | Infrastructure load testing |
| Security | Spot check only | Full penetration testing |

---

## Test Cases

### Category 1: Core Query Functionality

**TC-001: In-scope query returns a grounded response with citations**

- **Precondition:** User is authenticated via Teams. Agent is available in the Meridian Teams environment.
- **Test step:** Submit the query "What are an organisation's obligations under Article 13 of the EU AI Act?"
- **Expected result:** Agent returns a response grounded in the EU AI Act document. Response includes at least one citation linking to a document in the SharePoint knowledge base. Response does not contain content not found in the knowledge base.
- **Acceptance criteria:** Response returned within 10 seconds. Citation link is functional. Response accurately reflects Article 13 content.
- **Result:** Pass
- **Notes:** Response time 4.2 seconds. Two citations returned. Content verified by Daniel Soh.

---

**TC-002: Paraphrased query returns relevant results**

- **Precondition:** Same as TC-001.
- **Test step:** Submit "What do we need to tell users when we deploy an AI tool to them?" (paraphrased, no exact terminology from source documents)
- **Expected result:** Agent returns a relevant response about transparency and information obligations. Hybrid search correctly resolves the paraphrase to Article 13 content.
- **Acceptance criteria:** Response is relevant to the query intent. At least one appropriate citation returned.
- **Result:** Pass
- **Notes:** Semantic search component resolved the paraphrase correctly. Response cited Article 13 and the Meridian internal transparency policy.

---

**TC-003: Query matched to corporate policy topic**

- **Precondition:** Meridian AI Usage Policy is in the knowledge base.
- **Test step:** Submit "Is ChatGPT an approved tool for client work?"
- **Expected result:** Agent returns a response referencing the Approved AI Tools Register or Meridian AI Usage Policy. Does not give a generic answer.
- **Acceptance criteria:** Response references a specific Meridian policy document. Citation links are correct.
- **Result:** Pass
- **Notes:** Agent cited the Approved AI Tools Register with a direct document link.

---

**TC-004: Multi-turn conversation maintains context**

- **Precondition:** Active conversation session in Teams.
- **Test step:** Step 1: Submit "What is a high-risk AI system under the EU AI Act?" Step 2: In the same conversation, submit "What obligations apply to it?"
- **Expected result:** The second query is understood in the context of the first. Agent responds with obligations applicable to high-risk AI systems, not generic obligations.
- **Acceptance criteria:** Response to step 2 is contextually correct without the user re-stating "high-risk AI system".
- **Result:** Pass
- **Notes:** Copilot Studio session variables retained context correctly.

---

### Category 2: Escalation Pathway

**TC-005: Out-of-scope query triggers escalation**

- **Precondition:** Agent is running. Daniel Soh is the configured escalation contact.
- **Test step:** Submit "What is Meridian's revenue forecast for FY26?"
- **Expected result:** Agent recognises the query as outside scope. Returns a message explaining it cannot help with this topic and that it is connecting the user with a specialist. Sends a Teams notification to Daniel Soh.
- **Acceptance criteria:** No AI-generated answer is provided for an out-of-scope query. Escalation notification is delivered.
- **Result:** Pass
- **Notes:** Escalation notification delivered within 8 seconds of query submission.

---

**TC-006: Low-confidence query triggers escalation rather than a poor response**

- **Precondition:** A query is designed that returns search results all scoring below 0.7 confidence.
- **Test step:** Submit "What are the requirements for deploying foundation models in regulated financial services in Singapore?" (topic not covered in the knowledge base)
- **Expected result:** Agent returns no AI-generated response. Instead, acknowledges the knowledge gap and escalates to SME.
- **Acceptance criteria:** No hallucinated response. Escalation triggered. Audit log records ConfidenceBand as Escalated.
- **Result:** Pass
- **Notes:** Confidence threshold correctly blocked the response. Audit record showed ConfidenceBand = Escalated.

---

**TC-007: Escalation audit record is complete**

- **Precondition:** TC-006 has been executed.
- **Test step:** Review the SharePoint Audit List for the record created by TC-006.
- **Expected result:** Record contains: UserUPN, Timestamp, QueryText, ConfidenceBand = Escalated, EscalatedTo = Daniel Soh.
- **Acceptance criteria:** All required fields populated. No null values in mandatory fields.
- **Result:** Pass

---

### Category 3: Audit Logging

**TC-008: Every interaction creates an audit record**

- **Precondition:** Auditor has read access to the SharePoint Audit List.
- **Test step:** Submit 10 queries of varied types (in-scope, out-of-scope, escalated). Review the audit list after each submission.
- **Expected result:** 10 audit records created, one per interaction.
- **Acceptance criteria:** 10 records present with matching timestamps. No interactions without a record.
- **Result:** Pass
- **Notes:** All 10 records created. Average logging latency 1.1 seconds.

---

**TC-009: Audit record contains all required fields**

- **Precondition:** At least one audit record exists from previous test cases.
- **Test step:** Review the audit record from TC-001.
- **Expected result:** Record contains all fields defined in the audit schema: SessionID, UserUPN, Timestamp, QueryText, ResponseSummary, SourceDocuments, ConfidenceBand, EscalatedTo, EnvironmentName.
- **Acceptance criteria:** No mandatory fields are null or empty. EnvironmentName = Test. SourceDocuments lists at least one citation.
- **Result:** Pass

---

**TC-010: Audit list is not accessible to general staff**

- **Precondition:** Test user account that is not in the Risk or Compliance AAD group.
- **Test step:** Attempt to navigate to the SharePoint Audit List URL directly as a general staff member.
- **Expected result:** Access denied. User sees a SharePoint permission error.
- **Acceptance criteria:** General staff cannot view audit records.
- **Result:** Pass

---

### Category 4: Performance

**TC-011: Response time under load**

- **Precondition:** Test environment. 15 UAT participants submit queries simultaneously.
- **Test step:** Coordinate 15 concurrent query submissions at the same moment.
- **Expected result:** All 15 responses returned within 15 seconds (acceptable degradation under load versus the 10-second target for single users).
- **Acceptance criteria:** No timeouts. No error responses. All responses grounded.
- **Result:** Pass
- **Notes:** Slowest response was 11.4 seconds under 15-user load. No timeouts.

---

**TC-012: Agent is available during business hours**

- **Precondition:** Production-equivalent Test environment.
- **Test step:** Submit a test query at the start, middle, and end of the business day across 5 business days.
- **Expected result:** Agent responds to all 15 test queries without error.
- **Acceptance criteria:** 15 of 15 queries responded to successfully.
- **Result:** Pass
- **Notes:** 15 of 15 successful. One maintenance window at 02:30 AEST (outside business hours) for index refresh.

---

### Category 5: Power BI Dashboard

**TC-013: Dashboard reflects audit data correctly**

- **Precondition:** At least 20 audit records exist from prior test cases. Power BI has refreshed.
- **Test step:** Compare query count on the Power BI Overview page against the raw count in the SharePoint Audit List.
- **Expected result:** Query count matches between the two sources.
- **Acceptance criteria:** Zero discrepancy in query count. Escalation rate percentage is correctly calculated.
- **Result:** Pass

---

**TC-014: Dashboard is accessible to Risk and Compliance roles**

- **Precondition:** Test account with Risk and Compliance AAD group membership.
- **Test step:** Access the Power BI dashboard via the shared workspace link.
- **Expected result:** Dashboard loads fully. All pages accessible. No permission errors.
- **Acceptance criteria:** Full dashboard access confirmed.
- **Result:** Pass

---

**TC-015: Dashboard is not accessible to general staff**

- **Precondition:** Test account without Risk and Compliance group membership.
- **Test step:** Attempt to access the Power BI dashboard via the shared workspace link.
- **Expected result:** Access denied. Power BI workspace permission error displayed.
- **Acceptance criteria:** General staff cannot access compliance data.
- **Result:** Pass

---

## Defects Raised During UAT

| ID | Description | Severity | Resolution | Status |
|---|---|---|---|---|
| DEF-001 | Citation link in response opened a SharePoint permission error for users not in the AI Practice group | Medium | SharePoint library permissions updated to allow all staff read access to the AI-Governance-KB library | Closed |
| DEF-002 | Power BI dashboard showed incorrect escalation rate (dividing by total conversations including multi-turn turns, not unique sessions) | Medium | DAX measure corrected to count distinct SessionID values | Closed |
| DEF-003 | Adaptive card for SME escalation notification displayed raw JSON instead of formatted card in some Teams clients | Low | Card payload updated to Teams-compatible Adaptive Card schema v1.4 | Closed |

---

## UAT Sign-Off

All 15 test cases passed. Three defects were raised and resolved before sign-off. UAT participants confirmed the agent meets the business requirements defined in the Discovery document.

| Name | Role | Sign-off date |
|---|---|---|
| Elena Marchetti | Chief Risk Officer | Week 7 |
| Daniel Soh | Head of AI Practice | Week 7 |
| Sarah Kim | Senior Consultant (UAT lead) | Week 7 |

**UAT outcome: Approved for Production deployment.**

---

*Document version 1.0. Prepared by Arsh Chowdhury, Technology Consultant. Simulated engagement for portfolio purposes.*
