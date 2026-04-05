---
description: "Quality gate obligatorio antes de merge a main para SaMD Clase B."
---

# /quality-gate-iec62304

## 🚪 Gates & Inputs
- **Input:** Pull Request ID.
- **Enforcer:** `iec62304-auditor`.
- **Pre-requisites:** All unit tests in `apps/backend/tests` passing.

## 🚀 Steps
1. **Clinical Architecture Scan:** Verify no framework imports (FastAPI, SQLAlchemy) exist within `apps/backend/src/engines/`.
2. **Determinism Check:** Run `pytest` specifically on `apps/backend/tests/unit/engines` to verify input/output consistency.
3. **Traceability Validation:** Ensure every new function maps to a Requirement ID in the PR body.
4. **SOUP Verification:** Ensure no unapproved third-party dependencies were introduced in `pyproject.toml`.
5. **Human Adjudicator Sign-off:** Await confirmation from the `Clinical Director` role.

## ✅ Success/Failure Criteria
- **Success:** All tests green (`pytest` pass) + Clinical Approval -> Branch is unlocked for merge.
- **Failure:** Any step fails, pytest fails, or VETO issued by `iec62304-auditor`.

## 🔄 Rollback Strategy
- Automatic PR rejection.
