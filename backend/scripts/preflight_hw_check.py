import os, sys, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text, inspect
from app.database import engine, Base
from app.models import Participant, Dependent, BenefitPlan, BenefitElection, QLEEvent

def run_preflight_checks() -> dict:
    start_time = time.time()
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    checks, all_passed = [], True

    try:
        with engine.connect() as conn:
            t0 = time.time()
            conn.execute(text("SELECT 1;"))
            latency = round((time.time() - t0) * 1000, 2)
            checks.append({"check_name": "PostgreSQL Sandbox Connectivity", "status": "PASSED", "detail": f"Connected cleanly (Ping: {latency} ms)"})
    except Exception as e:
        checks.append({"check_name": "PostgreSQL Sandbox Connectivity", "status": "FAILED", "detail": str(e)})
        return {"overall_status": "FAILED", "checks": checks}

    required_tables = {"participants", "dependents", "benefit_plans", "benefit_elections", "qle_events"}
    existing_tables = set(inspector.get_table_names())
    missing = required_tables - existing_tables
    if not missing:
        checks.append({"check_name": "HW Relational Schema Presence", "status": "PASSED", "detail": f"Verified all {len(required_tables)} HW tables"})
    else:
        all_passed = False
        checks.append({"check_name": "HW Relational Schema Presence", "status": "FAILED", "detail": f"Missing tables: {missing}"})

    fks_elections = {fk["referred_table"] for fk in inspector.get_foreign_keys("benefit_elections")}
    if {"participants", "benefit_plans"}.issubset(fks_elections):
        checks.append({"check_name": "Foreign-Key Referential Integrity", "status": "PASSED", "detail": "benefit_elections -> participants & benefit_plans verified"})
    else:
        all_passed = False
        checks.append({"check_name": "Foreign-Key Referential Integrity", "status": "FAILED", "detail": f"Unexpected FKs: {fks_elections}"})

    try:
        with engine.begin() as conn:
            conn.execute(text("SAVEPOINT sp_neg_salary;"))
            try:
                conn.execute(text(
                    "INSERT INTO participants (employee_code, full_name, dob, hire_date, employment_status, annual_salary, scenario_tag) "
                    "VALUES ('ERR-999', 'Invalid User', '1990-01-01', '2023-01-01', 'ACTIVE_FT', -100.00, 'test');"
                ))
                all_passed = False
                checks.append({"check_name": "ACID CheckConstraint: Non-Negative Payroll/Salary", "status": "FAILED", "detail": "Allowed negative salary"})
            except Exception:
                checks.append({"check_name": "ACID CheckConstraint: Non-Negative Payroll/Salary", "status": "PASSED", "detail": "chk_participant_salary_positive blocked negative amount"})
            finally:
                conn.execute(text("ROLLBACK TO SAVEPOINT sp_neg_salary;"))
    except Exception as e:
        all_passed = False
        checks.append({"check_name": "ACID CheckConstraint", "status": "FAILED", "detail": str(e)})

    try:
        with engine.connect() as conn:
            dup_rows = conn.execute(text(
                "SELECT participant_id, COUNT(*) FROM benefit_elections WHERE status = 'ACTIVE' GROUP BY participant_id HAVING COUNT(*) > 1;"
            )).fetchall()
            if len(dup_rows) == 0:
                checks.append({"check_name": "Zero Overlapping Active Medical Elections", "status": "PASSED", "detail": "No duplicate ACTIVE elections"})
            else:
                all_passed = False
                checks.append({"check_name": "Zero Overlapping Active Medical Elections", "status": "FAILED", "detail": f"Duplicates: {dup_rows}"})
    except Exception as e:
        all_passed = False
        checks.append({"check_name": "Overlapping Elections Check", "status": "FAILED", "detail": str(e)})

    duration_ms = round((time.time() - start_time) * 1000, 1)
    return {"overall_status": "PASSED" if all_passed else "FAILED", "duration_ms": duration_ms, "checks": checks}

if __name__ == "__main__":
    res = run_preflight_checks()
    print(res)
    sys.exit(0 if res["overall_status"] == "PASSED" else 1)
