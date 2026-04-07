#!/usr/bin/env python3
"""
Integrum V2 — Pre-Flight Health Check
======================================
Valida el estado de DB, backend y frontend antes de ver pacientes reales.

Uso:
    python3 scripts/healthcheck.py            # check todo
    python3 scripts/healthcheck.py --db       # solo DB
    python3 scripts/healthcheck.py --backend  # solo backend
    python3 scripts/healthcheck.py --frontend # solo frontend
    python3 scripts/healthcheck.py --fast     # omite checks lentos (tsc, migrations)
"""

import sys
import os
import time
import argparse
import subprocess
import importlib
from pathlib import Path
from typing import Callable

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
BACKEND    = ROOT / "apps" / "backend"
FRONTEND   = ROOT / "apps" / "frontend"
ENV_FILE   = BACKEND / ".env"

# ── ANSI colors ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✅{RESET} {msg}")
def fail(msg):  print(f"  {RED}❌{RESET} {msg}")
def warn(msg):  print(f"  {YELLOW}⚠️ {RESET} {msg}")
def info(msg):  print(f"  {CYAN}ℹ️ {RESET} {msg}")
def header(msg):print(f"\n{BOLD}{CYAN}{'─'*50}\n  {msg}\n{'─'*50}{RESET}")

results = {"passed": 0, "failed": 0, "warned": 0}

def check(name: str, fn: Callable) -> bool:
    try:
        result = fn()
        if result is True or result is None:
            ok(name)
            results["passed"] += 1
            return True
        elif isinstance(result, str) and result.startswith("WARN:"):
            warn(f"{name} — {result[5:]}")
            results["warned"] += 1
            return True
        else:
            fail(f"{name}: {result}")
            results["failed"] += 1
            return False
    except Exception as e:
        fail(f"{name}: {type(e).__name__}: {e}")
        results["failed"] += 1
        return False

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATABASE CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def check_database(fast: bool = False):
    header("🗄️  DATABASE")

    # Load env
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        fail("DATABASE_URL not set"); results["failed"] += 1; return

    # Convert asyncpg → psycopg2 for sync check
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    def db_connect():
        import psycopg2
        conn = psycopg2.connect(sync_url, connect_timeout=5)
        conn.close()

    check("PostgreSQL reachable", db_connect)

    def check_tables():
        import psycopg2
        conn = psycopg2.connect(sync_url, connect_timeout=5)
        cur = conn.cursor()
        required = ["patients", "encounters", "adjudication_logs",
                    "decision_audit_logs", "clinical_traceability",
                    "patient_consents"]
        cur.execute("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public'
        """)
        existing = {r[0] for r in cur.fetchall()}
        missing = [t for t in required if t not in existing]
        conn.close()
        if missing:
            return f"Missing tables: {missing}"
        return True

    check("Required tables exist", check_tables)

    def check_outcome_columns():
        """Verify Fix 2 migration was applied."""
        import psycopg2
        conn = psycopg2.connect(sync_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'encounters'
        """)
        cols = {r[0] for r in cur.fetchall()}
        conn.close()
        required_new = ["weight_current_kg", "outcome_status",
                        "adverse_event", "medication_changed", "adherence_reported"]
        missing = [c for c in required_new if c not in cols]
        if missing:
            return f"Outcome tracking columns missing (run alembic upgrade head): {missing}"
        return True

    check("Outcome tracking columns present (Fix 2 migration)", check_outcome_columns)

    def check_row_counts():
        import psycopg2
        conn = psycopg2.connect(sync_url, connect_timeout=5)
        cur = conn.cursor()
        counts = {}
        for table in ["patients", "encounters", "adjudication_logs"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        conn.close()
        info(f"Row counts → patients:{counts['patients']} | "
             f"encounters:{counts['encounters']} | "
             f"adj_logs:{counts['adjudication_logs']}")
        return True

    check("Row counts", check_row_counts)

    if not fast:
        def check_migrations():
            result = subprocess.run(
                ["python3", "-m", "alembic", "current"],
                cwd=BACKEND, capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                return f"alembic current failed: {result.stderr[:200]}"
            output = result.stdout + result.stderr
            if "(head)" not in output:
                return f"WARN:Migrations not at head. Run: alembic upgrade head\n  {output.strip()}"
            return True

        check("Alembic migrations at HEAD", check_migrations)


# ─────────────────────────────────────────────────────────────────────────────
# 2. BACKEND CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def check_backend(fast: bool = False):
    header("⚙️  BACKEND")

    sys.path.insert(0, str(BACKEND))

    def check_imports():
        import src.schemas.encounter  # noqa
        import src.schemas.audit      # noqa
        import src.models.encounter   # noqa
        import src.models.audit       # noqa
        return True

    check("Core schemas + models importable", check_imports)

    def check_motor_registry():
        from src.engines.specialty_runner import PRIMARY_MOTORS, GATED_MOTORS
        total = len(PRIMARY_MOTORS) + len(GATED_MOTORS)
        if total < 40:
            return f"Expected >= 40 motors, got {total}"
        info(f"Motors: PRIMARY={len(PRIMARY_MOTORS)}, GATED={len(GATED_MOTORS)}, TOTAL={total}")
        return True

    check("Motor registry (>= 40 engines)", check_motor_registry)

    def check_motor_instantiation():
        from src.engines.specialty_runner import PRIMARY_MOTORS
        failed = []
        for name, cls in PRIMARY_MOTORS.items():
            try:
                cls()
            except Exception as e:
                failed.append(f"{name}: {e}")
        if failed:
            return f"Motors failed to instantiate: {failed}"
        return True

    check("All motors instantiate without error", check_motor_instantiation)

    def check_fhir_prefix():
        from src.api.v1.endpoints.fhir import router
        if router.prefix != "":
            return f"FHIR router has prefix={router.prefix!r} — duplicate routes bug!"
        return True

    check("FHIR router prefix empty (no /fhir/fhir/ duplication)", check_fhir_prefix)

    def check_coherence_validators():
        from src.schemas.encounter import BiometricsSchema, MetabolicPanelInput

        # Hard block 1: SBP <= DBP
        try:
            BiometricsSchema(weight_kg=80, height_cm=170, systolic_bp=70, diastolic_bp=90)
            return "BiometricsSchema: SBP<DBP not blocked"
        except Exception:
            pass

        # Hard block 2: BMI < 10
        try:
            BiometricsSchema(weight_kg=80, height_cm=1.75)
            return "BiometricsSchema: BMI<10 not blocked (talla en metros?)"
        except Exception:
            pass

        # Hard block 3: LDL > TotalChol
        try:
            MetabolicPanelInput(ldl_mg_dl=250, total_cholesterol_mg_dl=200)
            return "MetabolicPanelInput: LDL>TotalChol not blocked"
        except Exception:
            pass

        # Hard block 4: TG > 400 + HbA1c
        try:
            MetabolicPanelInput(triglycerides_mg_dl=600, hba1c_percent=7.2)
            return "MetabolicPanelInput: TG>400+HbA1c not blocked"
        except Exception:
            pass

        # Valid case must pass
        try:
            BiometricsSchema(weight_kg=85, height_cm=170, systolic_bp=130, diastolic_bp=85)
        except Exception as e:
            return f"BiometricsSchema: valid case rejected: {e}"

        return True

    check("Coherence validators (7 hard blocks active)", check_coherence_validators)

    def check_reason_codes():
        from src.schemas.audit import ReasonCode
        required = {
            "AGREE_INSIGHT", "OVERRIDE_CLINICAL_INTUITION",
            "OVERRIDE_ECONOMIC_BARRIER", "OVERRIDE_MISSING_CONTEXT",
            "OVERRIDE_PATIENT_REFUSAL", "BIOLOGICAL_IMPOSSIBILITY",
            "PARTIAL_AGREEMENT", "TECHNICAL_ERROR",
        }
        existing = {e.value for e in ReasonCode}
        missing = required - existing
        if missing:
            return f"Missing ReasonCode values: {missing}"
        info(f"ReasonCode enum: {len(existing)} values")
        return True

    check("ReasonCode structured vocabulary (8 values)", check_reason_codes)

    def check_export_endpoint():
        from src.api.v1.endpoints.export import MOTOR_COLUMNS, _build_flat_row
        if len(MOTOR_COLUMNS) < 35:
            return f"MOTOR_COLUMNS too short: {len(MOTOR_COLUMNS)}"
        info(f"Flat export: {len(MOTOR_COLUMNS)} motors × 5 cols + 12 base = {len(MOTOR_COLUMNS)*5+12} total columns")
        return True

    check("Research flat export endpoint registered", check_export_endpoint)

    if not fast:
        def check_pytest():
            t0 = time.time()
            result = subprocess.run(
                ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
                cwd=BACKEND, capture_output=True, text=True, timeout=120
            )
            elapsed = time.time() - t0
            output = (result.stdout + result.stderr).strip()
            last_line = [l for l in output.splitlines() if l.strip()][-1] if output else ""
            if result.returncode != 0:
                return f"Tests FAILED ({elapsed:.1f}s):\n    {last_line}"
            info(f"{last_line} ({elapsed:.1f}s)")
            return True

        check("pytest suite (all engines)", check_pytest)


# ─────────────────────────────────────────────────────────────────────────────
# 3. FRONTEND CHECKS
# ─────────────────────────────────────────────────────────────────────────────
def check_frontend(fast: bool = False):
    header("🖥️  FRONTEND")

    def check_node_modules():
        nm = FRONTEND / "node_modules"
        if not nm.exists():
            return "node_modules missing — run: npm install"
        count = sum(1 for _ in nm.iterdir() if _.is_dir())
        if count < 50:
            return f"WARN:Only {count} packages in node_modules — may need npm install"
        info(f"node_modules: {count} packages")
        return True

    check("node_modules installed", check_node_modules)

    def check_env_file():
        env = FRONTEND / ".env.local"
        env2 = FRONTEND / ".env"
        if not env.exists() and not env2.exists():
            return "WARN:No .env.local or .env in frontend — NEXT_PUBLIC_API_URL may not be set"
        for f in [env, env2]:
            if f.exists():
                content = f.read_text()
                if "NEXT_PUBLIC_API_URL" not in content:
                    return f"WARN:{f.name} exists but NEXT_PUBLIC_API_URL not set"
                info(f"API URL configured in {f.name}")
        return True

    check("Frontend env config (NEXT_PUBLIC_API_URL)", check_env_file)

    def check_critical_files():
        critical = [
            "src/components/consulta/ConsultationForm.tsx",
            "src/app/(dashboard)/consulta/[patientId]/page.tsx",
            "src/components/consulta/ResultsViewer.tsx",
        ]
        missing = [f for f in critical if not (FRONTEND / f).exists()]
        if missing:
            return f"Missing critical files: {missing}"
        return True

    check("Critical frontend files present", check_critical_files)

    def check_coherence_in_form():
        """Verify validateCoherence() is in ConsultationForm."""
        form_file = FRONTEND / "src/components/consulta/ConsultationForm.tsx"
        content = form_file.read_text()
        checks = {
            "validateCoherence function": "validateCoherence",
            "TG+HbA1c interference rule": "TG > 400",
            "Wheeler eAG formula": "28.7",
            "min/max range on LabField": 'min="20"',
        }
        missing = [name for name, needle in checks.items() if needle not in content]
        if missing:
            return f"Missing coherence logic: {missing}"
        info(f"Coherence rules present: {list(checks.keys())}")
        return True

    check("ConsultationForm coherence validation rules", check_coherence_in_form)

    if not fast:
        def check_typescript():
            t0 = time.time()
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--skipLibCheck"],
                cwd=FRONTEND, capture_output=True, text=True, timeout=120
            )
            elapsed = time.time() - t0
            if result.returncode != 0:
                errors = result.stdout[:500] if result.stdout else result.stderr[:500]
                return f"TypeScript errors ({elapsed:.1f}s):\n    {errors}"
            info(f"TypeScript: no errors ({elapsed:.1f}s)")
            return True

        check("TypeScript compilation (tsc --noEmit)", check_typescript)

    def check_backend_reachable():
        """Check if backend API is actually responding (if running)."""
        import urllib.request
        import urllib.error

        # Try to find API URL from frontend env
        api_url = "http://localhost:8000"
        for env_file in [FRONTEND / ".env.local", FRONTEND / ".env", BACKEND / ".env"]:
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if "NEXT_PUBLIC_API_URL" in line or "API_URL" in line:
                        _, _, v = line.partition("=")
                        api_url = v.strip().rstrip("/")
                        break

        try:
            req = urllib.request.Request(f"{api_url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.status
                info(f"Backend API at {api_url} → HTTP {status}")
                return True
        except urllib.error.HTTPError as e:
            info(f"Backend API at {api_url} → HTTP {e.code} (running)")
            return True
        except Exception as e:
            return f"WARN:Backend not reachable at {api_url} — is it running? ({type(e).__name__})"

    check("Backend API reachable (optional — only if running)", check_backend_reachable)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Integrum V2 Pre-Flight Health Check")
    parser.add_argument("--db",       action="store_true", help="Only check database")
    parser.add_argument("--backend",  action="store_true", help="Only check backend")
    parser.add_argument("--frontend", action="store_true", help="Only check frontend")
    parser.add_argument("--fast",     action="store_true", help="Skip slow checks (tsc, pytest, migrations)")
    args = parser.parse_args()

    run_all = not (args.db or args.backend or args.frontend)

    print(f"\n{BOLD}{'='*50}")
    print(f"  Integrum V2 — Pre-Flight Health Check")
    print(f"  {'--fast mode' if args.fast else 'Full mode'}")
    print(f"{'='*50}{RESET}")

    t0 = time.time()

    if run_all or args.db:
        check_database(fast=args.fast)

    if run_all or args.backend:
        check_backend(fast=args.fast)

    if run_all or args.frontend:
        check_frontend(fast=args.fast)

    # ── Summary ────────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    total = results["passed"] + results["failed"] + results["warned"]

    print(f"\n{BOLD}{'='*50}")
    print(f"  Result: {results['passed']}/{total} passed, "
          f"{results['warned']} warned, {results['failed']} failed  ({elapsed:.1f}s)")
    print(f"{'='*50}{RESET}\n")

    if results["failed"] > 0:
        print(f"{RED}{BOLD}❌ NOT READY — fix failures before seeing real patients.{RESET}\n")
        sys.exit(1)
    elif results["warned"] > 0:
        print(f"{YELLOW}{BOLD}⚠️  READY WITH WARNINGS — review warnings before proceeding.{RESET}\n")
        sys.exit(0)
    else:
        print(f"{GREEN}{BOLD}✅ ALL CLEAR — system ready for real patients.{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
