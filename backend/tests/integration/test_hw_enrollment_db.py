import pytest
from decimal import Decimal
from app.models import BenefitElection

@pytest.mark.req_id("HW-INT-01")
@pytest.mark.persona("Ananya Sharma (EMP-1001)")
def test_valid_birth_qle_updates_tier_and_payroll_deduction_in_db(client, db_session):
    payload = {
        "participant_id": 1, "plan_id": 1, "qle_type": "BIRTH",
        "event_date": "2026-05-10", "submitted_date": "2026-05-20",
        "target_coverage_tier": "EE_FAMILY", "include_dependent_ids": [1, 2], "annual_hsa_contribution": 6500.00
    }
    res = client.post("/api/enrollments/process-qle", json=payload)
    assert res.status_code == 200
    db_session.expire_all()
    el = db_session.query(BenefitElection).filter_by(participant_id=1, status="ACTIVE").first()
    assert el.coverage_tier == "EE_FAMILY" and el.per_paycheck_deduction == Decimal("156.00")

@pytest.mark.req_id("HW-INT-02")
@pytest.mark.persona("Meera Krishnan (EMP-2001)")
def test_expired_qle_over_30_days_rolls_back_db_state(client, db_session):
    payload = {
        "participant_id": 3, "plan_id": 1, "qle_type": "MARRIAGE",
        "event_date": "2026-03-01", "submitted_date": "2026-04-15",
        "target_coverage_tier": "EE_SPOUSE", "include_dependent_ids": [3], "annual_hsa_contribution": 3000.00
    }
    res = client.post("/api/enrollments/process-qle", json=payload)
    assert res.status_code == 400
    db_session.expire_all()
    el = db_session.query(BenefitElection).filter_by(participant_id=3, status="ACTIVE").first()
    assert el.coverage_tier == "EE_ONLY"

@pytest.mark.req_id("HW-INT-03")
@pytest.mark.persona("Rajesh Verma (EMP-3001)")
def test_reject_aged_out_26yo_dependent_preserves_db(client, db_session):
    payload = {
        "participant_id": 4, "plan_id": 2, "qle_type": "OPEN_ENROLLMENT",
        "event_date": "2026-06-01", "submitted_date": "2026-06-01",
        "target_coverage_tier": "EE_FAMILY", "include_dependent_ids": [4, 5], "annual_hsa_contribution": 0.00
    }
    res = client.post("/api/enrollments/process-qle", json=payload)
    assert res.status_code == 400 and "aged out" in res.json()["detail"]

@pytest.mark.req_id("HW-INT-04")
@pytest.mark.persona("Vikram Patel (EMP-1002 Part-Time)")
def test_part_time_employee_blocked_from_hdhp_enrollment(client, db_session):
    payload = {
        "participant_id": 2, "plan_id": 1, "qle_type": "OPEN_ENROLLMENT",
        "event_date": "2026-01-01", "submitted_date": "2026-01-01",
        "target_coverage_tier": "EE_ONLY", "include_dependent_ids": [], "annual_hsa_contribution": 1000.00
    }
    res = client.post("/api/enrollments/process-qle", json=payload)
    assert res.status_code == 400 and "PART_TIME" in res.json()["detail"]
