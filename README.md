# BenefitForge — Health & Welfare (HW) Eligibility & Life-Event Test Studio

A full-stack QA and test-orchestration studio for **Health & Welfare benefits administration**. It lets benefits teams, QA engineers, and compliance reviewers seed realistic participant data, validate that eligibility rules are enforced correctly, simulate mid-year life-event changes, and produce audit-ready verification reports — all against a real PostgreSQL database.

---

## What is BenefitForge?

BenefitForge is a **sandbox and safety net** for Health & Welfare (HW) benefits logic. Instead of trusting that eligibility rules "should" work, it proves it:

- It stands up a **safe, isolated PostgreSQL sandbox** pre-loaded with realistic, HIPAA-safe participant personas.
- It runs **automated compliance diagnostics** against the database before any testing begins.
- It provides a **live simulator** where you can trigger a Qualifying Life Event (marriage, birth, loss of coverage) and watch the database update — or safely roll back — in real time.
- It executes a **full test suite** and generates an auditable verification matrix (Markdown, CSV, JSON) that maps every test to a requirement and a business persona.

Think of it as a **pre-production proving ground** for the rules that decide who gets which benefits and how much they pay.

---

## Who this is for

| Audience | What they get |
| --- | --- |
| **Benefits / HR Operations** | Confidence that elections, coverage tiers, and payroll deductions are computed correctly before they reach production. |
| **Compliance & Audit** | Evidence that every rule is covered by an automated test, exportable as spreadsheet-ready reports. |
| **QA / SDET Engineers** | A ready-made, deterministic test environment with unit and database-integration coverage plus a UI to explore edge cases. |
| **Engineering Leads** | A clear, enforced contract for the domain rules, backed by both application logic and database constraints. |
| **Product Owners** | A tangible demo of the eligibility engine and the exact scenarios it protects against. |

---

## The problem it solves

Health & Welfare platforms are governed by strict, easy-to-get-wrong rules (dependent age-outs, life-event deadlines, HSA caps, employment eligibility). One mistake means wrongly denied coverage, payroll errors, or regulatory findings.

BenefitForge turns those rules into **executable, verifiable tests** and makes each one **visible and interactive**, so problems are caught in a sandbox long before they reach real members.

---

## Core capabilities

| Capability | Description |
| --- | --- |
| **HIPAA-safe cohort seeding** | Deterministically resets and repopulates the sandbox with fictional personas covering open enrollment, life events, part-time exclusion, and age-out boundaries. No real member data is ever used. |
| **Pre-flight compliance diagnostics** | Automated database health checks: connectivity, schema presence, referential integrity, ACID constraint enforcement, and duplicate-election detection. |
| **Live QLE simulator** | Configure a Qualifying Life Event, execute it, and view a side-by-side **Before / After** database state diff with recalculated payroll deductions. |
| **Atomic transactions with rollback** | Every invalid election is rejected with a clear reason and the database is returned to its prior state — never a partial write. |
| **Audit-ready verification matrix** | The full test suite emits `.md`, `.csv`, and `.json` reports mapping each test to a requirement ID and a business persona. |
| **One-command environment** | A single Docker Compose command launches the database, API, and Studio UI — pre-diagnosed and pre-seeded. |

---

## The HW rules enforced

These are the domain invariants BenefitForge verifies, enforced in **both** business logic and PostgreSQL constraints.

| # | Rule | Plain-English summary |
| --- | --- | --- |
| 1 | **Dependent age-out (ACA 26)** | A `CHILD` dependent becomes ineligible once they reach age **26** on the coverage effective date, unless flagged as disabled. |
| 2 | **QLE 30-day window** | `MARRIAGE`, `BIRTH`, and `LOSS_OF_COVERAGE` changes must be submitted within **0–30 days** of the event. `OPEN_ENROLLMENT` bypasses the window. |
| 3 | **Employment status eligibility** | Only **full-time (ACTIVE_FT)** employees may enroll in medical (HDHP/PPO) plans and contribute to an HSA. Part-time employees are blocked. |
| 4 | **Statutory HSA contribution cap** | Annual HSA contributions may not exceed **$4,300** (employee-only) or **$8,550** (family tiers), enforced in logic and by a database `CheckConstraint`. |
| 5 | **Non-negative payroll deductions** | Per-paycheck (26 pay periods/year) and annual amounts must be **>= $0.00**, computed as `(base_monthly_ee x tier_multiplier x 12) / 26`. |

Tier multipliers used in payroll math: `EE_ONLY 1.00`, `EE_CHILD 1.65`, `EE_SPOUSE 1.90`, `EE_FAMILY 2.60`.

---

## How it works — the four-stage workflow

1. **Set up test data** — Seed a cohort of participant personas into the sandbox.
2. **Check the environment** — Run pre-flight diagnostics to confirm the database is compliant and healthy.
3. **Simulate a life event** — Execute a QLE election and inspect the atomic Before/After database diff.
4. **Verify and export** — Run the full test suite and download the audit-ready verification matrices.

Each stage is available in the **Studio UI**, the **REST API**, and as a **command-line script**.

---

## Quick Start

### Option A — Docker (recommended, one command)

Requirements: Docker Desktop with Docker Compose.

```powershell
docker compose up -d --build
```

That single command builds and starts the PostgreSQL sandbox, the FastAPI backend, and the React Studio UI. On startup the backend automatically runs the pre-flight diagnostics and seeds the sandbox.

| Service | URL |
| --- | --- |
| Studio UI | http://localhost:5173 |
| Backend API docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | `localhost:5434` (container port 5432) |

Stop everything with:

```powershell
docker compose down
```

### Option B — Local development

Requirements: **Python 3.11** (the pinned dependencies do not build on newer interpreters), Node 18+, and Docker for the database.

```powershell
# 1. Start just the database
docker compose up -d hw_db

# 2. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/preflight_hw_check.py
python scripts/seed_hw_data.py --scenario all
python -m pytest -v
uvicorn app.main:app --reload --port 8000

# 3. Frontend (second terminal)
cd frontend
npm install
npm run dev
```

The `.env` file at the repository root controls database connectivity. By default it maps the sandbox to host port `5434` to avoid collisions with a locally installed PostgreSQL; CI uses the standard `5432`.

---

## Using the Studio UI

Open http://localhost:5173. The studio is organized into four side-by-side panels.

**1. Test Data Setup — HIPAA-Safe Cohorts.** Click a scenario button to (re)seed the sandbox. The participant registry table below shows each persona, employment status, dependents (with ages and age-out warnings), active coverage tier, and per-paycheck deduction.

**2. Environment Setup — Pre-Flight DB Checks.** Click **Run DB Diagnostics** for a pass/fail table of connectivity, schema, referential-integrity, ACID-constraint, and duplicate-election checks, plus diagnostic latency.

**3. Live QLE Simulator & Atomic DB State Diff Viewer.** Pick a participant (clicking a row in the table loads them), choose a benefit plan, life-event type, target coverage tier, event and submission dates, HSA amount, and which dependents to include. Click **Execute QLE & Assert Atomic DB Mutation**.
- On success you get a side-by-side **Before / After** card showing the tier and payroll-deduction change.
- On any rule violation you get an **ATOMIC ROLLBACK EXECUTED** banner with the exact reason, and the database is untouched.

**4. Automated Test Execution & Result Matrix.** Click **Run Full Pytest Suite** to execute the entire unit and database-integration suite. The panel shows total/passed/failed counters and a results table (requirement ID, persona, suite, test case, status, latency), with buttons to download the matrix as `.md`, `.csv`, or `.json`.

### Pre-loaded personas

| Code | Persona | Scenario exercised |
| --- | --- | --- |
| `EMP-1001` | Ananya Sharma (Active FT) | BIRTH QLE; adds spouse + newborn, upgrades to family tier. |
| `EMP-1002` | Vikram Patel (Part-Time) | Medical/HSA enrollment correctly **blocked**. |
| `EMP-2001` | Meera Krishnan (Active FT) | MARRIAGE QLE and 30-day window expiry. |
| `EMP-3001` | Rajesh Verma (Active FT) | Dependent age-out: one child aged 26 (blocked) and one aged 22 (eligible). |

---

## Using the REST API

Interactive docs are served at http://localhost:8000/docs.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness probe. |
| `GET` | `/api/participants` | Participant registry plus available benefit plans. |
| `POST` | `/api/enrollments/process-qle` | Validate and atomically apply a life-event election. |
| `POST` | `/api/sandbox/seed` | Reset and seed a cohort (`all`, `open_enrollment`, `qle_life_events`, `dependent_age_out`). |
| `POST` | `/api/sandbox/preflight` | Run the pre-flight database compliance diagnostics. |
| `POST` | `/api/sandbox/run-tests` | Execute the full pytest suite and return the verification matrix. |
| `GET` | `/api/sandbox/reports` | Fetch the latest verification matrices (JSON + Markdown + CSV). |

Example — simulate a birth and upgrade to family coverage:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/enrollments/process-qle `
  -ContentType 'application/json' -Body '{
    "participant_id": 1,
    "plan_id": 1,
    "qle_type": "BIRTH",
    "event_date": "2026-05-10",
    "submitted_date": "2026-05-20",
    "target_coverage_tier": "EE_FAMILY",
    "include_dependent_ids": [1, 2],
    "annual_hsa_contribution": 6500.00
  }'
```

A successful response includes `before_state` and `after_state` snapshots; a rejected request returns HTTP `400` with a `detail` explaining the rule that failed.

---

## Command-line tools

Run from the `backend` directory:

| Command | Description |
| --- | --- |
| `python scripts/preflight_hw_check.py` | Database diagnostics; exits non-zero on failure (CI-friendly). |
| `python scripts/seed_hw_data.py --scenario all` | Seed a cohort (`--scenario` accepts `all`, `open_enrollment`, `qle_life_events`, `dependent_age_out`). |
| `python -m pytest -v` | Run the full unit + integration suite and regenerate the verification matrices. |
| `uvicorn app.main:app --reload --port 8000` | Start the API with auto-reload. |

---

## Verification matrix & audit reports

Every test run writes three files into `backend/reports/`:

| File | Format | Use |
| --- | --- | --- |
| `hw_verification_matrix.md` | Markdown | Human-readable summary table with total/passed counters. |
| `hw_verification_matrix.csv` | CSV | Spreadsheet import for audit evidence. |
| `hw_verification_matrix.json` | JSON | Structured ingest for CI pipelines. |

Each row records the **requirement ID**, **business persona**, **suite** (Unit or Integration (DB)), **test case**, **status**, **latency (ms)**, and error detail. Tests are traceable via `@pytest.mark.req_id` and `@pytest.mark.persona` markers.

### Test coverage

| Req ID | Persona / Rule | What is verified |
| --- | --- | --- |
| `HW-UNIT-01` | Child turning 26 | Dependent is eligible the day before the 26th birthday and ineligible on it. |
| `HW-UNIT-02` | Disabled adult child | Disabled children are exempt from the age-26 limit. |
| `HW-UNIT-03` | Mid-year QLE filer | The 30-day QLE window boundary (day 30 passes, day 31 fails). |
| `HW-UNIT-04` | HDHP subscriber | HSA statutory limits for single vs. family tiers. |
| `HW-UNIT-05` | Payroll proration | 26-pay-period deduction math. |
| `HW-INT-01` | `EMP-1001` | Valid birth QLE updates tier and deduction in the database. |
| `HW-INT-02` | `EMP-2001` | Expired QLE rolls the database back to its prior state. |
| `HW-INT-03` | `EMP-3001` | Aged-out 26-year-old dependent is rejected. |
| `HW-INT-04` | `EMP-1002` | Part-time employee is blocked from HDHP enrollment. |

---

## Verified working

**Verification date: 2026-10-18** — full stack run via `docker compose up -d --build` (Python 3.11, PostgreSQL 16):

- Pre-flight diagnostics: **5/5 checks passed** (connectivity, schema, referential integrity, ACID constraint, duplicate elections).
- Seeding produced the expected cohort: **4 participants, 5 dependents, 3 active elections**.
- Test suite: **9/9 passed** — both directly via `pytest` and through `POST /api/sandbox/run-tests`.
- Happy path: a BIRTH QLE moved `EMP-1001` from `EE_ONLY` to `EE_FAMILY` and recalculated the per-paycheck deduction from `$60.00` to `$156.00`, atomically.
- Rejection paths all returned HTTP `400` with the correct reason: part-time enrollment, aged-out dependent, HSA cap exceeded, and expired QLE window.
- Studio UI served HTTP `200` and the report export endpoints returned the generated matrices.

---

## Architecture & tech stack

**Backend** — Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL 16 (psycopg2), Pytest + HTTPX TestClient, Tabulate.
**Frontend** — React 18, Vite.
**DevOps** — Docker Compose, GitHub Actions CI (pre-flight, seed, tests, and report upload on every push/PR).

```
benefitforge-hw-test-studio/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes and QLE transaction orchestration
│   │   ├── models.py            # SQLAlchemy models + CheckConstraints
│   │   ├── schemas.py           # Pydantic request/response contracts
│   │   ├── config.py            # .env-driven configuration
│   │   ├── database.py          # Engine / session factory
│   │   └── services/eligibility.py   # The HW rule engine
│   ├── scripts/
│   │   ├── seed_hw_data.py      # HIPAA-safe cohort seeding
│   │   └── preflight_hw_check.py# SQL compliance diagnostics
│   ├── tests/
│   │   ├── conftest.py          # Fixtures + verification-matrix generation hooks
│   │   ├── unit/                # Pure rule-engine unit tests
│   │   └── integration/         # Database-backed API tests
│   └── reports/                 # Generated .md / .csv / .json matrices
├── frontend/
│   └── src/App.jsx              # The four-panel Studio UI
├── docker-compose.yml
└── .github/workflows/hw-test-ci.yml
```

---

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `HW_DB_PORT` | `5432` (`.env` sets `5434`) | Host port mapped to the PostgreSQL container. |
| `DATABASE_URL` | auto-derived from `HW_DB_PORT` | Full SQLAlchemy connection string. |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL the Studio UI calls. |

---

## Further documentation

- [flow.md](flow.md) — end-to-end data flow, service sequence, and the audit-matrix pipeline.
- [decesions.md](decesions.md) — architectural decisions, root-cause analyses, and bug fixes.
- [AGENTS.md](AGENTS.md) — condensed context for LLM/developer onboarding.

---

## Troubleshooting

- **Connection/password errors against `localhost:5432`** — a native PostgreSQL service may already occupy port 5432. The sandbox maps to `5434` (via `HW_DB_PORT` in `.env`); connect with `DATABASE_URL` from `.env`.
- **`pip install` fails building `psycopg2` / `pydantic-core`** — use Python **3.11**; the pinned versions have no wheels for newer interpreters. Running via Docker avoids this entirely.
- **`FileNotFoundError` when running tests from the UI** — resolved internally by invoking `[sys.executable, "-m", "pytest"]` instead of a bare `pytest`.
- **`version` is obsolete warning on `docker compose`** — harmless Compose warning regarding the `version:` key in `docker-compose.yml`.

