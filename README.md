# BenefitForge: Health & Welfare (HW) Eligibility & Life-Event Test Studio

A full-stack QA & SDET orchestration platform engineered for **Health and Welfare (HW) Tech** benefits administration systems.

## Quick Start (PowerShell)
1. `docker compose up -d hw_db`
2. `cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
3. `python scripts/preflight_hw_check.py; python scripts/seed_hw_data.py --scenario all; pytest -v`
4. `uvicorn app.main:app --reload --port 8000`
5. In a second PowerShell window: `cd frontend; npm install; npm run dev`
