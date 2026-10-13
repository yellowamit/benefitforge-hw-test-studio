import os, csv, json, time, pytest
from tabulate import tabulate
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from scripts.seed_hw_data import seed_hw_database

test_records = []

@pytest.fixture(scope="function", autouse=True)
def reset_hw_sandbox():
    seed_hw_database("all")
    yield

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        req_m = item.get_closest_marker("req_id")
        persona_m = item.get_closest_marker("persona")
        test_records.append({
            "requirement_id": req_m.args[0] if req_m else "HW-REQ-GEN",
            "persona": persona_m.args[0] if persona_m else "System Rule",
            "suite": "Unit" if "unit" in item.nodeid else "Integration (DB)",
            "test_case": item.nodeid.split("::")[-1],
            "status": "PASSED" if report.passed else "FAILED",
            "duration_ms": round(report.duration * 1000, 2),
            "error_detail": str(report.longrepr) if report.failed else "Verified"
        })

def pytest_sessionfinish(session, exitstatus):
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "hw_verification_matrix.json"), "w") as f:
        json.dump(test_records, f, indent=2)
    if test_records:
        with open(os.path.join(reports_dir, "hw_verification_matrix.csv"), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(test_records[0].keys()))
            writer.writeheader()
            writer.writerows(test_records)
    headers = ["Req ID", "Persona", "Suite", "Test Case", "Status", "Latency (ms)"]
    rows = [[r["requirement_id"], r["persona"], r["suite"], r["test_case"], r["status"], r["duration_ms"]] for r in test_records]
    total, passed = len(test_records), sum(1 for r in test_records if r["status"] == "PASSED")
    md = f"# BenefitForge — Health & Welfare Verification Matrix
**Total:** {total} | **Passed:** {passed}

{tabulate(rows, headers=headers, tablefmt='github')}
"
    with open(os.path.join(reports_dir, "hw_verification_matrix.md"), "w") as f:
        f.write(md)
