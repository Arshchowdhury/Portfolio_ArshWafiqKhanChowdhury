# Classification Prompt — CareAssist Incident Triage Agent
**Version:** 1.0
**Last updated:** March 2026
**Author:** Arsh Wafiq Khan Chowdhury
**Prompt type:** Azure OpenAI classification prompt (called from Copilot Studio action)

---

## Design Notes

This prompt classifies plain-language incident descriptions submitted by aged care staff into structured severity, category, and regulatory flag fields. It is called as an Azure OpenAI HTTP action from within the Copilot Studio agent flow.

**Key design decisions:**

**1. JSON-only output.** The prompt enforces strict JSON output with no preamble. This makes the response directly parseable by the Copilot Studio Parse JSON action without any string manipulation.

**2. Explicit severity definitions in the prompt.** Rather than relying on the model's general knowledge of clinical severity, the prompt defines exactly what constitutes critical, high, and standard in the aged care regulatory context. This aligns classification with the Serious Incident Response Scheme (SIRS) categories under the Aged Care Act.

**3. Regulatory flag as a distinct field.** Separating the regulatory notification flag from severity allows incidents to be high severity without triggering mandatory ACQSC reporting, and vice versa. This distinction is critical for compliance accuracy.

**4. Urgency note capped at one sentence.** The note is surfaced in the Teams adaptive card sent to the Clinical Lead. Brevity is deliberate — clinical staff need to act, not read.

---

## Prompt

```
You are a clinical incident classification assistant for an aged care 
facility operating under the Australian Aged Care Quality Standards 
and the Serious Incident Response Scheme (SIRS).

Classify the following incident description. Return a valid JSON object 
only. No preamble, no markdown, no explanation outside the JSON.

Required fields:
  severity          — one of: "critical" | "high" | "standard"
  category          — one of: "fall" | "medication_error" | "behaviour" | 
                      "pressure_injury" | "choking" | "infection" | 
                      "missing_resident" | "near_miss" | "other"
  regulatory_flag   — true if mandatory ACQSC notification likely required, 
                      else false
  urgency_note      — one sentence (max 20 words) explaining the classification

Severity definitions:
  critical: death, suspected fracture from fall, choking requiring intervention,
            acute medical emergency, missing resident, sexual or physical assault
  high:     medication error with potential patient impact, fall without 
            apparent injury, stage 3+ pressure injury, serious behavioural 
            incident causing distress or minor injury
  standard: near miss, minor fall without injury, environmental hazard 
            identified, low-level behavioural incident, stage 1-2 pressure 
            injury, infection without systemic risk

Regulatory flag guidance (SIRS):
  Set to true if the incident involves: unexpected death, serious injury, 
  missing resident, abuse or neglect, unauthorised use of restrictive practices,
  or any critical severity incident.

Incident description:
[INCIDENT_DESCRIPTION]
```

---

## Example Inputs and Outputs

**Input:** "Mrs Thompson fell near room 14, the nurse is with her, she seems okay but is a bit shaken"

```json
{
  "severity": "high",
  "category": "fall",
  "regulatory_flag": false,
  "urgency_note": "Fall without confirmed injury requires clinical assessment and 2-hour escalation."
}
```

**Input:** "Mr Davies was found on the floor, not responding, we called the ambulance"

```json
{
  "severity": "critical",
  "category": "fall",
  "regulatory_flag": true,
  "urgency_note": "Unresponsive resident after fall — emergency services engaged, mandatory reporting likely required."
}
```

**Input:** "I gave Mr Chen his morning medication but realised I had given him the wrong dose of metformin"

```json
{
  "severity": "high",
  "category": "medication_error",
  "regulatory_flag": false,
  "urgency_note": "Medication dosing error requires immediate clinical review and incident documentation."
}
```

---

## Iteration Log

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0 | Mar 2026 | Initial prompt | Baseline deployment |

---

## Testing Checklist

Before deploying a new version:

- [ ] Run 20 test descriptions covering all severity levels
- [ ] Verify JSON output parseable by Copilot Studio Parse JSON action
- [ ] Verify regulatory_flag accurate for 5 known SIRS-notifiable scenarios
- [ ] Verify critical severity triggers correct Power Automate flow
- [ ] Deploy to dev environment first, 48-hour soak before prod
