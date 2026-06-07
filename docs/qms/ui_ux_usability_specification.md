# UI/UX Design & Usability Specification
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Usability Standard:** IEC 62366-1:2015 (Application of usability engineering to medical devices)
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Purpose
This document defines the user interface (UI) design requirements, user experience (UX) profiles, and usability engineering specifications for **Integrum V2** in accordance with **IEC 62366-1**. It ensures that the software interface minimizes use errors and is optimized for clinical environments.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial UI/UX and usability engineering design specification. |

---

## 2. User Profiles & Context of Use (IEC 62366-1 §5.1)

### 2.1 Intended User Profiles
*   **Specialist Clinician (Endocrinologist/Bariatrician):** High clinical expertise; requires detailed metric visualization, clinical citations, and raw calculation outputs (e.g., biological age acceleration, HOMA-IR).
*   **General Practitioner (GP) / Family Physician:** Requires high-level alerts, clear laboratory optimization recommendations, and automated risk scoring to decide on referrals or treatment pathways.
*   **Clinical Staff / Nurses (Intake):** Responsible for fast demographic data entry, vital signs, and loading lab results. Requires high usability in form completion.

### 2.2 Context of Use
*   **Environment:** Clinical consultation offices, hospital wards, or outpatient clinics.
*   **Key Constraints:** High-pressure environment, limited time per patient consultation (typically 15–20 minutes), varying lighting conditions.
*   **Visual Priority:** Text legibility, prominent alarms for critical indicators, and high contrast.

---

## 3. UI Design System & Aesthetics

### 3.1 Color Palette & Semantics
The color system must feel premium, modern, and high-contrast, with clear visual hierarchy.

| Token | HSL / Hex Code | Usage | Clinical Meaning |
|---|---|---|---|
| **Primary (Brand)** | `hsl(220, 80%, 50%)` | Main buttons, navigation | Standard action |
| **Success / Safe** | `hsl(142, 70%, 45%)` | Normal values, checklist done | Normal physiological state |
| **Warning / Probable** | `hsl(35, 90%, 50%)` | Borderlines, mid-level risks | Requires clinical monitoring |
| **Alert / Critical** | `hsl(0, 85%, 60%)` | Out-of-bounds, severe risk | Active safety gate (e.g., PHQ-9 suicide risk) |
| **Background Dark** | `hsl(222, 47%, 11%)` | Primary layout (Dark Mode) | Minimizes eye strain during long shifts |
| **Background Light** | `hsl(0, 0%, 98%)` | Primary layout (Light Mode) | High contrast for well-lit rooms |

### 3.2 Typography & Hierarchy
*   **Font Family:** `Geist Sans` or `Inter` (sans-serif) for tabular data, labels, and system texts to ensure readability.
*   **Size Hierarchy:**
    *   Page Title: `24px` / Bold (Single `h1` per screen for SEO and screen reader accessibility).
    *   Card Headings: `16px` / Semi-bold.
    *   Data Readings: `14px` / Monospace (`Fira Code` or similar) for tabular numerical data to prevent alignment shift.

---

## 4. User Interface Architecture & Navigation

The Next.js application is structured into three primary visual areas:

```
┌────────────────────────────────────────────────────────┐
│  Side Navigation Bar (Dashboard, Intake, History, QMS) │
├────────────────────────────────────────────────────────┤
│  Top Bar: Selected Patient Context, Age/Sex, Sync Status│
├────────────────────────────────────────────────────────┤
│  Main Work Area:                                       │
│                                                        │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │   Intake & Forms Panel│   │   Real-time Alerts   │  │
│  └───────────────────────┘   └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Obesity Phenotypes & Risk Dashboard            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Laboratory Recommendations & Stewardship       │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 4.1 Intake Interface (T0 Flow)
*   **Live Input Validation:** As fields are filled (e.g., Systolic Blood Pressure), visual tooltips must display if values exceed physiological bounds (e.g., SBP $>200$ mmHg).
*   **Autosave Indicator:** A micro-animation shows real-time local sync status (e.g., "Saved Locally" / "Synced to EHR").

### 4.2 Clinical Result Panels
*   **Acosta Phenotypes:** Displayed as a radial radar chart to visualize overlap between categories (Hungry Brain vs. Hungry Gut).
*   **Laboratory Suggestions Checklists:** Grouped into collapsible accordion components based on priority (High, Medium, Low) with a one-click EHR request action.

---

## 5. Use Error Mitigation & Safety Gates (IEC 62366-1 §5.2)

### 5.1 Use Error 1: Wrong Demographic Entry
*   **Mitigation:** The system displays a confirmation dialog if the biological sex is changed while existing gender-specific data is present (e.g., "Changing sex to male will disable Women's Health Motor evaluations. Confirm?").

### 5.2 Use Error 2: Overlooking Critical Patient Risks
*   **Mitigation:** If `PHQ-9` psychometric evaluation shows a positive response on Item 9 (Suicidal Ideation), a red warning banner floats persistently at the top of the interface and requires the clinician to check a mitigation box ("Safety protocol triggered") before exporting the clinical note.

### 5.3 Use Error 3: Typographical Data Entry Errors
*   **Mitigation:** Text fields for numeric physiological data block letters and only allow decimal numbers within predefined logical range boundaries. Inputs outside of logical bounds are highlighted in red and disable the "Save" and "Export" triggers.

---

## 6. Usability Testing & Verification Protocol

*   **Formative Evaluations:** Heuristic analysis by UX designers and testing with 3 medical users to identify high-cognitive-load screens.
*   **Summative Usability Testing (Validation):** Executed with at least 15 representative clinical users performing simulated scenarios (e.g., patient intake, checking lab warnings, exporting FHIR bundles).
*   **Pass Criteria:** Zero critical use errors that could lead to diagnostic delay or pharmacological mismatch.
