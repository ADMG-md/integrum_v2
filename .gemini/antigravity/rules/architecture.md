# Architectural Integrity Rules

These rules prevent the degradation of the repository structure and ensure clean architecture.

## Clean Architecture Enforcement
- **Trigger**: Creation of new directories or structural changes in `apps/`.
- **Action**: You MUST invoke the `repo-structure-auditor` skill to verify that the change follows the Clean Architecture domain boundaries.
- **Restriction**: No framework-specific imports (FastAPI, SQLAlchemy) are allowed inside the clinical engine domain (`apps/backend/src/engines/`).

## Monorepo Dependency Guard
- **Trigger**: Changes to `pyproject.toml` or addition of cross-app dependencies.
- **Action**: Verify that shared contracts in `data-contracts/` are the only allowed way to share types between Frontend and Backend.
