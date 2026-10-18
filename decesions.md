# BenefitForge — Major Engineering Decisions & Bug Fixes (`decesions.md`)

This document records the architectural decisions, bug diagnoses, root causes, and resolutions implemented across the **BenefitForge Health & Welfare Test Studio**.

---

## Decision 1: Multiline f-string Syntax Error in Pytest Hook (`conftest.py`)
- **Issue**: Running `pytest -v` or any test suite resulted in an immediate fatal crash:
  `SyntaxError: unterminated f-string literal (detected at line 58) in tests/conftest.py`.
- **Root Cause**: In `backend/tests/conftest.py`, lines 58–62 attempted to create a multiline string using a single pair of double quotes `f"# BenefitForge..."` spanning multiple lines instead of triple quotes `f"""..."""`.
- **Resolution**: Converted the report template string to `f"""# BenefitForge — Health & Welfare Verification Matrix ... """`.
- **Consequence**: Pytest collects and executes test suites cleanly without syntax termination errors.

---

## Decision 2: Cross-Platform Subprocess Test Execution via `sys.executable`
- **Issue**: Triggering test execution from the Studio UI via `POST /api/sandbox/run-tests` failed when `pytest` was not registered on the system's global `$PATH` environment variable.
- **Root Cause**: `subprocess.run(["pytest", "-v"])` relied on `pytest` being an executable discoverable in Windows PATH. In virtualenvs or Python environments where Scripts directories are not added to PATH, this throws `FileNotFoundError: [WinError 2]`.
- **Resolution**: Replaced `["pytest", "-v"]` with `[sys.executable, "-m", "pytest", "-v"]` in `app/main.py`.
- **Consequence**: Test execution succeeds reliably across all platforms, virtual environments, and CI runners regardless of global PATH settings.

---

## Decision 3: Host Port Collision Resolution (`HW_DB_PORT`)
- **Issue**: Attempting to start PostgreSQL container or connect to `localhost:5432` failed with authentication errors (`FATAL: password authentication failed for user "hw_admin"`).
- **Root Cause**:
  1. A native Windows PostgreSQL 18 service (`postgresql-x64-18`) was running on the host machine listening on `0.0.0.0:5432`.
  2. Because the host Windows networking stack prioritizes native Windows service sockets over Docker WSL2 port proxies on IPv4 `127.0.0.1:5432`, requests intended for the Dockerized `benefitforge_sandbox` were routed to the host Windows service which had different credentials.
- **Resolution**:
  1. Updated `docker-compose.yml` to allow host port mapping override: `ports: - "${HW_DB_PORT:-5432}:5432"`.
  2. Updated `backend/app/config.py` with `python-dotenv` integration to automatically load `.env` from workspace root and dynamic fallback: `f"postgresql://hw_admin:hw_secret@localhost:{os.getenv('HW_DB_PORT', '5432')}/benefitforge_sandbox"`.
  3. Created `.env` with `HW_DB_PORT=5434` and `DATABASE_URL=postgresql://hw_admin:hw_secret@localhost:5434/benefitforge_sandbox`.
  4. Preserved default `5432:5432` for clean CI environments (GitHub Actions Ubuntu runners).
- **Consequence**: Zero port collision on local developer machines while maintaining 100% backward compatibility with clean Docker/CI environments.

---

## Decision 4: UTF-8 Explicit Encoding for File I/O Across Windows/Linux
- **Issue**: Reading or writing verification matrix reports (`.md`, `.json`, `.csv`) containing Unicode symbols (such as em dashes `—` or currency symbols) risk `UnicodeEncodeError` / `UnicodeDecodeError` on Windows systems using default non-UTF-8 locale encodings (`cp1252` / `Windows-1252`).
- **Root Cause**: Python's `open()` without explicit `encoding="utf-8"` defaults to system locale on Windows.
- **Resolution**: Added `encoding="utf-8"` explicitly across:
  - `conftest.py` report generation (`open(..., "w", encoding="utf-8")`)
  - `main.py` report readers (`open(..., "r", encoding="utf-8")`)
- **Consequence**: Deterministic character preservation across all operating systems without platform-specific encoding crashes.

---

## Decision 5: Dynamic Plan & Dependent Selection in Studio UI
- **Issue**: The original React UI:
  1. Hardcoded `include_dependent_ids: []` in the QLE simulation request, preventing any user from testing dependent age-out validation or dependent enrollments from the UI.
  2. Discarded `plans` returned by `/api/participants`, hardcoding `plan_id: 1` without allowing users to switch between HDHP and PPO plans.
  3. Omitted `EE_CHILD` from coverage tier dropdown and `LOSS_OF_COVERAGE` from QLE type dropdown.
  4. Rendered `$null` or `$undefined` if a participant had no prior election.
- **Resolution**:
  1. Added `plans` state and a dynamic Plan selector with clear indicators of monthly base rate and HSA eligibility.
  2. Added dynamic dependent checkboxes with age calculation on event date, visually tagging ACA age-out boundary violations (`Age >= 26`).
  3. Added `EE_CHILD` tier and `LOSS_OF_COVERAGE` QLE options.
  4. Fixed diff box formatting to handle un-enrolled participants with null values gracefully.
- **Consequence**: The studio UI now fully mirrors and exercises the entire domain rule engine and database constraints interactively.

---

## Decision 6: Community Wisdom Reference
- Guided by developer community best practices on Docker, PostgreSQL port collisions, and FastAPI/SQLAlchemy integration (see `Community Wisdom` section in `AGENTS.md` and conversation summary).
- Re-mapping host ports (`5434:5432`) while keeping internal container networking on `5432` is the recommended, zero-friction pattern for multi-project development workstations.
