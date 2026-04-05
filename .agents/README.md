# .agents/ — Agent Skills & Workflows

This directory contains specialized skills and workflows for the Integrum V2 CDSS project.

## Structure

```
.agents/
├── skills/                    # Specialized agent capabilities
│   ├── iec62304-auditor/      # IEC 62304 Class B compliance (VETO power)
│   ├── iso13485-qms/          # Change control and QMS traceability
│   ├── clinical-validity-engineer/  # Clinical evidence (GRADE) to code
│   ├── repo-structure-auditor/      # Clean Architecture enforcement
│   ├── test-coverage-auditor/       # 100% engine test coverage
│   ├── clinical-safety-officer/     # FDA 21 CFR Part 11, HIPAA, drug safety
│   └── data-contracts-auditor/      # Frontend/backend contract enforcement
├── workflows/                 # Multi-step processes
│   ├── quality-gate-iec62304.md    # Pre-merge quality gate
│   └── workflow-change-control.md  # ISO 13485 change control
└── scripts/                   # Executable enforcement scripts
    ├── check_pure_python.sh        # Verify no framework imports in engines
    ├── check_test_coverage.py      # Verify 100% motor test coverage
    └── check_risk_sync.py          # Verify risk file sync with motors
```

## How Skills Work

Each skill is a YAML-frontmatter markdown file that defines:
- **name**: Unique identifier
- **description**: What the skill does
- **triggers**: When the skill activates (file changes, labels, PR events)
- **enforces**: Standards it enforces (IEC62304, ISO13485, etc.)
- **checks**: Specific validations it performs
- **enforce**: Action on failure (`veto_on_failure`, `require_clinical_signoff`)

## Skill Inventory (7 skills)

| Skill | What it does | Trigger |
|---|---|---|
| **iec62304-auditor** | IEC 62304 Class B compliance with VETO power | PR, engine changes, deployment |
| **iso13485-qms** | Change control and QMS traceability | PR, bugs, incidents |
| **clinical-validity-engineer** | Clinical evidence (GRADE) to code translation | Feature requests, evidence files |
| **repo-structure-auditor** | Clean Architecture enforcement | Branch creation, PR |
| **test-coverage-auditor** | 100% engine test coverage verification | PR, engine/test changes |
| **clinical-safety-officer** | FDA 21 CFR Part 11, HIPAA, drug safety | PR, safety-critical files |
| **data-contracts-auditor** | Frontend/backend contract enforcement | PR, schema/type changes |

## Workflow Composition

- **quality-gate-iec62304** → Runs before every merge to main
- **workflow-change-control** → Runs for any significant change

## Enforcement Scripts

Executable scripts for CI/CD integration:

```bash
# Check engines are pure Python (no FastAPI/SQLAlchemy)
.agents/scripts/check_pure_python.sh

# Verify 100% test coverage for registered motors
python .agents/scripts/check_test_coverage.py

# Verify risk management file is in sync with motors
python .agents/scripts/check_risk_sync.py
```

## Review Cadence

Skills should be reviewed **monthly** to ensure they reflect:
- Current project state (motor count, file structure)
- Updated clinical evidence and guidelines
- New regulatory requirements

**Last reviewed:** 2026-04-04
**Next review:** 2026-05-04
