# AGENTS.md — BenefitForge LLM & Developer Context

## 1. Domain & Purpose
**BenefitForge** is a Full-Stack Health & Welfare (HW) Eligibility, Open Enrollment, and Qualifying Life Event (QLE) Test Orchestration Studio.
It demonstrates two core engineering pillars:
1. **Test Data & Environment Setup**: HIPAA-safe deterministic cohort seeding (`scripts/seed_hw_data.py`) and automated SQL pre-flight compliance diagnostics (`scripts/preflight_hw_check.py`).
2. **Test Execution & Result Analysis**: Multi-layer unit and database-backed integration tests (`tests/`) with custom Pytest hooks that generate audit-ready verification matrices in Markdown, JSON, and CSV (`reports/`).

## 2. Tech Stack & Environment
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0+, Pydantic v2, PostgreSQL 16 (psycopg/psycopg2)
- **Testing**: Pytest, HTTPX TestClient, Tabulate
- **Frontend**: React 18, Vite, modern CSS (muted sage/emerald accessible palette)
- **DevOps**: Docker Compose, GitHub Actions CI
- **Configuration**: Dynamic `.env` configuration supporting `HW_DB_PORT` (defaults to 5432 in CI, 5434 in local environment with native Postgres port conflict).

## 3. Core Health & Welfare Domain Invariants
1. **Dependent Age-Out Rule (ACA 26-Year Boundary)**: Dependents with relationship `CHILD` are strictly ineligible if their age on the coverage effective date is `>= 26`. Exempt if `is_disabled == True`.
2. **Qualifying Life Event (QLE) 30-Day Window**: Mid-year election changes (`MARRIAGE`, `BIRTH`, `LOSS_OF_COVERAGE`) must be submitted within `0` to `30` calendar days of `event_date`. `OPEN_ENROLLMENT` bypasses this check.
3. **Employment Status Eligibility**: Only `ACTIVE_FT` (Full-Time) employees can enroll in HDHP/PPO medical plans and contribute to an HSA. `PART_TIME` employees are blocked from medical/HSA elections.
4. **Statutory HSA Contribution Cap**: Annual HSA contributions cannot exceed `$4,300.00` for `EE_ONLY` or `$8,550.00` for family tiers (`EE_SPOUSE`, `EE_CHILD`, `EE_FAMILY`), enforced both in business logic and PostgreSQL `CheckConstraint`.
5. **Non-Negative Payroll Deductions**: Per-paycheck deductions (26 pay periods/year) and annual elections must be `>= 0.00`. Formulated as `(base_monthly_ee * multiplier * 12) / 26`.

## 4. Key Commands (PowerShell)
- Start PostgreSQL Sandbox: `docker compose up -d hw_db`
- Run Pre-Flight Checks: `cd backend; python scripts/preflight_hw_check.py`
- Seed Cohorts: `cd backend; python scripts/seed_hw_data.py --scenario all`
- Run Pytest & Generate Reports: `cd backend; python -m pytest -v`
- Start Backend API: `cd backend; uvicorn app.main:app --reload --port 8000`
- Start React Studio UI: `cd frontend; npm.cmd install; npm.cmd run dev`

## 5. Architectural Documents
- [flow.md](file:///c:/Users/mail2/Projects/benefitforge-hw-test-studio/flow.md): Complete application data flow, service layer sequence, and audit matrix pipeline.
- [decesions.md](file:///c:/Users/mail2/Projects/benefitforge-hw-test-studio/decesions.md): Major design decisions, bug fix root cause analyses, and architectural trade-offs.

## 6. Key Bug Fixes & Troubleshooting
- **Unterminated f-string (`conftest.py`)**: Fixed multiline f-string with triple quotes `f"""..."""`.
- **Subprocess pytest path**: Uses `[sys.executable, "-m", "pytest", "-v"]` in `trigger_pytest_execution` to work in all virtual environments.
- **Postgres port collision**: Avoids native port 5432 collision on host by mapping `HW_DB_PORT=5434` in `.env` while keeping container port 5432 and CI 5432.
- **Unicode file encoding**: Explicit `encoding="utf-8"` added to all JSON/CSV/Markdown file read/write routines.
