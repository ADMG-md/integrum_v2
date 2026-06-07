# Software Development & Configuration Management Plan
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Standard Reference:** IEC 62304 §5.1, §6 & §8 / ISO 13485 Clause 7.3
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Purpose
This document outlines the software development lifecycle, branch management strategy, release controls, configuration items, and maintenance processes for **Integrum V2**. It satisfies the requirements for the **Software Development Plan (SDP)** and **Software Configuration Management Plan (SCMP)** under IEC 62304.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial software development and configuration management plan. |

---

## 2. Software Development Lifecycle (SDLC)

Integrum V2 follows an Agile Scrum model adapted for medical device development, ensuring that safety gates and traceability audits are performed at every iteration sprint.

```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐
│ User/Clin.  │ ──> │ Clinical Req  │ ──> │ Code & Unit   │
│ Needs (PRD) │     │ (Traceability)│     │ Tests (pytest)│
└─────────────┘     └───────────────┘     └───────┬───────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌───────────────┐     ┌───────────────┐
│ Production  │ <── │ Validation &  │ <── │ Integration   │
│ Deployment  │     │ Usability     │     │ Test Gates    │
└─────────────┘     └───────────────┘     └───────────────┘
```

### 2.1 Key Phases
1.  **Requirement Specification:** Features are translated to clinical requirements, assigned a unique `SR-XXX` ID, and appended to the [traceability_matrix.md](file:///Users/antonymolinagarrido/Projects/integrum_v2/docs/qms/traceability_matrix.md).
2.  **Implementation & Unit Test:** Code is written alongside unit tests. No code is committed without matching test coverage.
3.  **Code Review & Quality Gates:** Verification testing is run automatically. Merge to `main` is gated by human peer review and 100% test pass status.
4.  **Verification and Validation (V&V):** Prior to release, full system verification (integration tests) and usability validation are executed.
5.  **Release and Maintenance:** Post-market clinical feedback is tracked to update system engines.

---

## 3. Configuration Management & Git Strategy

### 3.1 Branching Model (Gitflow Adaptation)
*   **`main` Branch:** Protected branch containing production-ready, validated code. Every commit on `main` is tagged with a release version (e.g., `v3.0.0`).
*   **`develop` Branch:** Integration branch for active feature development.
*   **Feature Branches (`feature/SR-XXX-...`):** Independent branches for implementing specific requirements. Must be named after the Clinical Requirement ID they solve.

### 3.2 Code Review & Pull Request Gates
All pull requests merging into `develop` or `main` require:
1.  Approval from at least one Clinical Safety Officer or Clinical Validity Engineer.
2.  Green build status from the automated CI/CD pipeline.
3.  Verification that [risk_management_file.md](file:///Users/antonymolinagarrido/Projects/integrum_v2/docs/qms/risk_management_file.md) has been updated if clinical math was modified.

---

## 4. Software Maintenance & Feedback Loop (IEC 62304 §6)

### 4.1 Feedback Collection & Bug Tracking
*   Clinical users submit feedback, use difficulties, or suspected calculation anomalies via an integrated support form.
*   Every submission is triaged by the technical team and assigned a severity level:
    *   **Level 1 (Critical Safety):** Incorrect risk scoring, failure of safety gates (e.g., PHQ-9 suicidal warning). Requires an immediate hotfix.
    *   **Level 2 (Usability/Data):** Data entry errors, slow response times. Addressed in the current sprint.
    *   **Level 3 (Cosmetic):** Layout alignment, minor copy edits. Addressed in future sprints.

### 4.2 Patching & Hotfix Procedure
For Level 1 Critical Safety issues:
1.  Create a hotfix branch from the active release tag on `main`.
2.  Apply the fix, update the risk management file, and write tests that reproduce and verify the fix.
3.  Deploy to the staging environment and execute full regression testing.
4.  Merge into `main` and deploy to production, increasing the patch version (e.g., `v3.0.0` $\rightarrow$ `v3.0.1`).
