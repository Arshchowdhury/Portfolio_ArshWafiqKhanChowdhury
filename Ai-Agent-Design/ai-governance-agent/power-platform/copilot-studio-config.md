# Copilot Studio Configuration Notes

This document describes how the AI Governance Advisory Agent is surfaced to end
users through Microsoft Copilot Studio, and how the studio topics map to the
Python backend.

Copilot Studio acts as the **conversation layer** — it handles user authentication,
conversation history, and topic routing.  All substantive question-answering is
delegated to the Python RAG engine via a direct Azure Function call or HTTP trigger,
depending on deployment topology.

---

## Environment

| Setting | Value |
|---|---|
| Environment type | Developer / Test / Production (never Default) |
| Authentication | Azure Active Directory — Required (org users only) |
| Channel | Microsoft Teams (primary), Web chat widget (secondary) |
| Language | English (en-AU) |

---

## Topics

### 1. Greeting

**Trigger phrases:**
- "Hello", "Hi", "Good morning", "What can you help me with?"

**Behaviour:**
Displays a welcome card explaining the agent's purpose and suggested question categories:
- EU AI Act requirements
- NIST AI Risk Management Framework
- Internal AI use policy
- AI risk assessment guidance
- General AI governance questions

No backend call — handled entirely within Copilot Studio.

---

### 2. Governance Question (primary topic)

**Trigger phrases:**
Free-text intent — any message not matching a specific topic falls here.

**Behaviour:**

```
Step 1 → Capture user message as {UserQuery}
Step 2 → Send HTTP POST to Azure Function / Power Automate flow
         Payload: { "query": "{UserQuery}", "session_id": "{ConversationId}" }
Step 3 → Parse JSON response
         Fields: response, confidence_band, escalated, citations[]
Step 4 → Branch on escalated:
           True  → Show escalation message + "The AI Practice team has been notified"
           False → Show Adaptive Card with:
                     - Response text
                     - Confidence band badge (High / Medium)
                     - Collapsible citations section
Step 5 → Prompt: "Was this helpful?" (Yes / No / Ask another question)
```

**Adaptive Card layout (simplified):**

```json
{
  "type": "AdaptiveCard",
  "body": [
    { "type": "TextBlock", "text": "{response}", "wrap": true },
    {
      "type": "FactSet",
      "facts": [
        { "title": "Confidence", "value": "{confidence_band}" },
        { "title": "Sources",    "value": "{citation_list}" }
      ]
    }
  ],
  "actions": [
    { "type": "Action.Submit", "title": "Helpful ✓" },
    { "type": "Action.Submit", "title": "Not helpful" },
    { "type": "Action.Submit", "title": "Ask another question" }
  ]
}
```

---

### 3. Escalation Acknowledgement

**Trigger:** Returned when `escalated: true` from backend.

**Behaviour:**
- Displays the escalation message from the backend
- Posts a notification to the `#ai-governance-escalations` Teams channel via
  Power Automate (using the same HTTP trigger that handles audit logging)
- Records the escalated query in the SharePoint audit list with `Escalated = Yes`

No further action from Copilot Studio — the AI Practice team picks up from Teams.

---

### 4. Feedback Collection

**Trigger:** User clicks "Not helpful" on a response Adaptive Card.

**Behaviour:**
- Prompts: "What was missing from the answer?"
- Captures free-text feedback as {FeedbackText}
- Logs to SharePoint list: `AI Governance Feedback`
  - Columns: Timestamp, SessionId, OriginalQuery, Feedback, Reviewed (Yes/No default No)
- Thanks the user and offers to rephrase the original question

---

### 5. Out of Scope

**Trigger phrases:**
- "Write me a policy", "Draft a contract", "Can you do X for me"
- Anything the intent classifier routes here for action-type requests

**Behaviour:**
Explains the agent answers governance questions only, and points the user to
the AI Practice team mailbox (`ai-practice@meridianadvisory.com.au`) for
advisory engagements.

---

## Power Automate Integration

The Copilot Studio HTTP action calls the following Power Automate flows:

| Flow | Purpose | Trigger |
|---|---|---|
| `AI-Gov-Query-Handler` | Routes query to Python RAG engine, returns response | HTTP POST from Copilot Studio |
| `AI-Gov-Audit-Logger` | Writes query/response record to SharePoint audit list | HTTP POST from Python audit_logger.py |
| `AI-Gov-Escalation-Notifier` | Posts Teams message on escalation | HTTP POST from Python audit_logger.py when escalated=true |

> **Note:** In a direct-integration topology, Copilot Studio calls the Python
> backend via Azure API Management (APIM) rather than through Power Automate.
> Power Automate is used here because it fits within a Microsoft 365 environment
> that may not have an Azure API Management instance provisioned.

---

## Generative Answers Node (optional)

Copilot Studio's native **Generative Answers** node can be configured to
point at the same Azure AI Search index as a fallback, providing a low-latency
path for simple factual lookups.

However, the Generative Answers node does not support:
- Custom confidence thresholds
- Structured citation output
- Audit logging
- Escalation routing

For this reason, the Python RAG engine is used as the primary answering path,
and the Generative Answers node is disabled in the primary governance topic to
avoid routing conflicts.

---

## Deployment Checklist

- [ ] Copilot Studio environment created (not Default)
- [ ] Azure AD authentication configured (Required sign-in)
- [ ] Teams channel connected and tested
- [ ] HTTP action endpoint URL updated with production Azure Function / APIM URL
- [ ] Adaptive Card JSON reviewed for Teams rendering compatibility
- [ ] Escalation Teams channel ID confirmed with IT
- [ ] SharePoint `AI Governance Feedback` list created
- [ ] End-to-end test: submit question → receive answer → click "Not helpful" → verify feedback logged
- [ ] UAT sign-off from AI Practice team lead
