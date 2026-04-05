#!/bin/bash

# SaMD Security Audit script (Mission 12 Hardening)
# This script performs a dependency scan and generates an SBOM.

echo "--- 🛡️ Starting Integrum V2 Security Audit ---"

# 1. Dependency Scan (Vulnerabilities)
echo "[1/3] Scanning dependencies for known vulnerabilities..."
source .venv/bin/activate
safety check --full-report > security_vuln_report.txt 2>&1

if [ $? -eq 0 ]; then
    echo "✅ No known security vulnerabilities found in dependencies."
else
    echo "⚠️ Vulnerabilities detected! Check security_vuln_report.txt for details."
fi

# 2. Generating SBOM (Software Bill of Materials)
echo "[2/3] Generating SBOM (Software Bill of Materials)..."
pip freeze > sbom_manifest.txt
echo "✅ SBOM generated at sbom_manifest.txt."

# 3. Environment Sanitization Check
echo "[3/3] Checking .env for potential leaks..."
grep -r "SECRET_KEY\|PASSWORD\|DATABASE_URL" src/ | grep -v "os.getenv" > potential_leaks.txt
if [ -s potential_leaks.txt ]; then
    echo "❌ SECURITY ALERT: Potential hardcoded secrets found in source! Check potential_leaks.txt."
else
    echo "✅ No hardcoded secrets detected in clinical source code."
    rm potential_leaks.txt
fi

echo "--- 🏁 Audit Complete ---"
