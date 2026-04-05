# IEC 62304 & Clinical Compliance Rules

These rules ensure that every clinical change is audited and follows SaMD Class B standards.

## IEC 62304 Strict Enforcement
- **Trigger**: Any modification to files in `apps/backend/src/engines/**` or `data-contracts/schemas/**`.
- **Action**: You MUST invoke the `iec62304-auditor` skill before proceeding with the changes.
- **Requirement**: Any clinical logic change requires a corresponding update to `docs/qms/risk_management_file.md` if the risk profile changes.

## Clinical Validity Guard
- **Trigger**: Any modification to Pydantic models in `apps/backend/src/schemas/**`.
- **Action**: You MUST invoke the `clinical-validity-engineer` skill to verify biological bounds (ge, le) and evidence mapping.

## QMS & ISO 13485 Traceability
- **Trigger**: Any PR or significant code change.
- **Action**: Ensure the PR/Commit description includes a reference to a Requirement ID or Issue. Invoke `iso13485-qms` to verify documentation sync.
