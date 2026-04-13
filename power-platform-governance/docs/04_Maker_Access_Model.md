# 04 — Maker Access Model

**Client:** Ridgeline Partners  
**Author:** Arsh Wafiq Khan Chowdhury  
**Status:** Accepted  

---

## Purpose

This document defines how Power Platform access is granted, reviewed, and revoked at Ridgeline Partners. It covers the Entra ID security group structure, the license assignment model, the maker onboarding workflow, and the quarterly access review process.

Access governance is the control that the DLP policy and Managed Environments cannot provide on their own. A connector policy governs what connectors can be combined. Access governance governs who can build anything at all, where, and with what level of permission.

---

## Guiding Principle

The goal is not to restrict Power Platform access — Ridgeline's maker culture is a business asset. The goal is to ensure that access is:

- **Intentional:** granted in response to a request, not inherited from a broad licence assignment
- **Appropriate:** the level of access matches the maker's role and experience
- **Auditable:** every access grant is traceable to a request and an approver
- **Revocable:** access is removed when a staff member changes roles or leaves

---

## Entra ID Security Group Structure

Access is managed through four Entra ID security groups. Group membership controls both environment access and licence assignment.

| Group name | Members | Access granted |
|---|---|---|
| `PP-Makers-Standard` | All licensed makers | Development environment (read/write), Sandbox allocation eligibility, Power Apps per-user licence |
| `PP-Makers-Senior` | Experienced makers with peer review responsibility | All Standard permissions + pull request review rights in GitHub, access to Test environment (read only) |
| `PP-Platform-Admin` | Platform team members | All environments (read/write), Admin Centre access, pipeline service principal credentials, DLP policy management |
| `PP-End-Users` | All staff | Production environment (run access to published apps only), no maker licence required |

Group membership is requested via the onboarding workflow (see below) and approved by the Head of Digital or the platform lead.

---

## Licence Assignment

Power Platform licences at Ridgeline are assigned per user, not per app. This is a deliberate choice — per-app licensing is lower cost for narrow use cases but creates a fragmented licensing estate that is difficult to administer as the number of apps grows.

| Licence | Assigned to | Assigned via |
|---|---|---|
| Power Apps per-user | Members of `PP-Makers-Standard` and above | Entra group-based assignment via Microsoft 365 Admin Centre |
| Power Automate per-user | Members of `PP-Makers-Standard` and above | As above |
| Power Apps per-app (fallback) | End users accessing a specific app where a per-user licence is not justified | Manual assignment on request |

Premium connector access (Dataverse, HTTP with Azure AD) is enabled for all makers in `PP-Makers-Standard` and above through the per-user licence.

The platform administrator reviews licence utilisation quarterly. Licences assigned to users who have not logged in within 90 days are flagged for review and potentially reassigned.

---

## Maker Onboarding Workflow

New makers follow this workflow before receiving access to the Development environment.

```
1. Staff member submits Microsoft Form: "Power Platform Maker Access Request"
   Fields: Name, manager, practice group, intended use, experience level (self-assessed)

2. Platform lead receives notification (Power Automate flow)
   Reviews request — approves or requests a conversation

3. On approval:
   a. Staff member is added to PP-Makers-Standard (or PP-Makers-Senior if appropriate)
   b. Power Apps and Power Automate per-user licences are assigned automatically via group
   c. Staff member receives welcome email with links to:
      - Ridgeline Power Platform style guide
      - Component library documentation
      - This governance framework (summary version)
      - Contact for the platform lead

4. Platform lead books a 30-minute orientation session within 5 business days
   Covers: solution structure, source control expectations, how to raise a pull request
```

The form and the automated licence assignment flow live in the `RidgelineOps` solution in the Development environment.

---

## Sandbox Allocation

Makers in `PP-Makers-Standard` and above may request a personal sandbox environment for prototyping or training.

- Sandboxes are Developer-tier environments (free, limited to 3GB storage)
- Provisioned via a Power Automate flow triggered by a maker request form
- Lifecycle: 30 days, renewable once per quarter per maker
- The sandbox is isolated from all ring environments — work cannot be promoted directly from a sandbox into Development without a manual export/import step
- Sandboxes that have not been accessed in 14 days are flagged for deletion

---

## Maker Offboarding

When a staff member leaves Ridgeline or changes to a role that does not require Power Platform access:

1. HR triggers the standard offboarding process in the HRIS system
2. A Power Automate flow monitors the HRIS for deactivated accounts and removes the user from all `PP-*` security groups within 24 hours
3. The platform lead reviews any active flows or apps owned by the departing user within 5 business days and reassigns ownership or decommissions them
4. Any sandbox environment owned by the departing user is deleted

Removing a user from the Entra groups revokes their environment access and licence assignment simultaneously.

---

## Quarterly Access Review

The platform administrator conducts a quarterly review covering:

- All members of `PP-Makers-Standard`, `PP-Makers-Senior`, and `PP-Platform-Admin`
- Last login date per user (sourced from Power Platform Admin Centre activity report)
- Licence utilisation (users with a licence who have not created or modified a solution in 90 days)
- Any flows or apps owned by users no longer in the firm

The review produces a report for the Head of Digital. Access for users who have been inactive for over 90 days is suspended pending confirmation from their manager.

---

## Sharing Limits (Managed Environments)

In Test and Production, Managed Environments sharing limits are configured as follows:

| Setting | Value |
|---|---|
| Canvas app sharing with security groups | Restricted to `PP-End-Users` and above |
| Canvas app sharing with external users | Blocked |
| Environment sharing with individuals outside Entra tenant | Blocked |

These controls are enforced by the Managed Environments policy, not by individual maker discretion. A maker in the Production environment cannot share an app externally even if they have the technical permission to attempt it.
