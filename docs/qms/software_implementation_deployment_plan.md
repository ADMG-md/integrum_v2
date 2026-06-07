# Software Implementation & Deployment Plan
**Project:** Integrum V2 — Clinical Decision Support System (CDSS) for Obesity and Cardiometabolic Health
**Classification:** Software as a Medical Device (SaMD) — IEC 62304 Class B
**Status:** DRAFT (TRL 5 Alignment)
**Last Updated:** 2026-06-07

---

## 1. Document Control & Scope

### 1.1 Purpose
This document defines the technical deployment strategy, hosting architecture, database initialization, and clinical site integration protocols for **Integrum V2**. It serves as the **Software Implementation Plan** under ISO 13485 Clause 7.5 and IEC 62304.

### 1.2 Version History
| Version | Date | Author | Description |
|---|---|---|---|
| 0.1 | 2026-06-07 | Antigravity AI (Pair Programming) | Initial software implementation and clinical site deployment plan. |

---

## 2. Infrastructure & Production Topology

The system is deployed using Docker containers orchestrated via `docker-compose` behind a Caddy reverse proxy to guarantee automated TLS management and service isolation.

```
                  ┌───────────────────────────────┐
                  │          Public Internet      │
                  └───────────────┬───────────────┘
                                  │ HTTPS (Port 443)
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ Host VPS (Ubuntu LTS / Alpine Linux)                            │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              Caddy 2 Proxy Container (caddy)            │   │
│   └─────────────┬─────────────────────────────┬─────────────┘   │
│                 │ (Port 8000)                 │ (Port 3000)     │
│                 ▼                             ▼                 │
│   ┌───────────────────────────┐ ┌───────────────────────────┐   │
│   │  FastAPI Backend (web)    │ │  Next.js Frontend (fe)    │   │
│   └─────────────┬─────────────┘ └───────────────────────────┘   │
│                 │                                               │
│                 ▼                                               │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │          PostgreSQL 16 Database Container (db)          │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 Component Configuration
*   **Proxy (`caddy`):** Directs traffic to `/api/*` to the FastAPI backend and all other requests to the Next.js frontend container. Handles automated SSL/TLS certificates.
*   **Backend (`web`):** Runs the FastAPI application on Uvicorn. Exposes clinical calculation engines.
*   **Frontend (`fe`):** Compiles and serves the Next.js application.
*   **Database (`db`):** PostgreSQL Alpine image with persistent volumes mapping clinical data and audit trails.

---

## 3. Deployment & Installation Protocol

### 3.1 Prerequisite Verification
Before triggering the deployment pipeline, target servers must satisfy:
1.  Docker Engine $\ge 24.0$ and Docker Compose $\ge 2.20$.
2.  Ports `80` (HTTP challenge) and `443` (HTTPS) open on the public firewall.
3.  Active DNS records pointing to the target domain (e.g., `integrum.coecaribe.org`).

### 3.2 Deployment Commands
```bash
# Clone the repository and navigate to root
git clone https://github.com/integrum-clinical/integrum_v2.git
cd integrum_v2

# Build and start all services in detached mode
docker-compose up -d --build

# Run Alembic migrations to initialize the schema
docker-compose exec web alembic upgrade head

# Seed required lookup tables and concepts
docker-compose exec web python -m scripts.seed_terminology
```

---

## 4. Clinical Site Integration Plan (COECaribe Pilot)

### 4.1 Phase 1: Local Clinical Trial Configuration
*   **Context:** Pilot deployment at COECaribe (Barranquilla, Colombia) under the "Colombia Inteligente 976" program.
*   **Data Integration:** Establish a secure IPSec VPN tunnel between the local EHR databases and the Integrum V2 VPS.
*   **Authentication Integration:** Configure SSO (Single Sign-On) using OpenID Connect (OIDC) with the clinic's local Active Directory.

### 4.2 Phase 2: FHIR R4 Integration
*   Establish bidirectional data sharing:
    1.  Integrum V2 fetches patient demographics and active medication lists from the clinic's HAPI FHIR server.
    2.  Upon finalization of a medical consultation, Integrum V2 generates a FHIR Bundle containing all calculated results and logs, exporting it back to the clinic's EHR repository.

---

## 5. Maintenance, Backup & Disaster Recovery

### 5.1 Backup Strategy
*   **Frequency:** Full database dump executed every 24 hours.
*   **Location:** Encrypted dumps (AES-256) uploaded to an offsite secure S3-compliant storage with a 30-day retention policy.
*   **Command:**
    ```bash
    docker-compose exec db pg_dump -U postgres integrum_prod | gpg --encrypt --recipient backup@integrum.org > backup_$(date +%F).sql.gpg
    ```

### 5.2 Rollback Protocol
If a deployment fails validation tests post-release:
1.  Stop the active services: `docker-compose down`.
2.  Checkout the last known stable tag: `git checkout tags/v3.0.0`.
3.  Rebuild and launch: `docker-compose up -d --build`.
4.  If schemas were modified, restore the database snapshot taken immediately before the migration.
