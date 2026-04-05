---
description: "Flujo formal de Change Control bajo ISO 13485 (FDA 21 CFR 820.30)."
---

# /workflow-change-control

## 🚪 Gates & Inputs
- **Input:** Proposed Change Description, Component (Frontend/Backend/Data Contracts).
- **Enforcer:** `iso13485-qms`.
- **Pre-requisites:** Change request approved by Product Owner.

## 🚀 Steps
1. **Risk Impact Assessment:** Determine if the change modifies physiological limits, database schemas, or clinical algorithms.
2. **Assign Class:**
   - Class A (No injury risk): UI improvements, internal refactors without data change.
   - Class B (Non-serious injury risk): Clinical engines, DB migrations, Schema changes.
3. **Traceability Creation:** Generate Ticket ID mapped to Requirements.
4. **Execution & Review:** Branch `feature/TicketID`, PR reviewed by respective Lead (Clinical/Technical).
5. **DHF Sign-off:** Change Control Board (CCB) approves merge.

## ✅ Success/Failure Criteria
- **Success:** PR merged with full DHF trace and CCB approval.
- **Failure:** Missing Risk Impact Assessment or CCB rejection.

## 🔄 Rollback Strategy
- Close PR, discard branch.
