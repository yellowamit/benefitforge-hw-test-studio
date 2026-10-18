import os, sys, json, subprocess
from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import Participant, Dependent, BenefitPlan, BenefitElection, QLEEvent
from app.schemas import QLEEnrollmentRequest, QLEEnrollmentResponse, ElectionSnapshot, SeedRequest
from app.services.eligibility import (
    is_dependent_eligible,
    validate_qle_window,
    validate_hsa_statutory_limit,
    calculate_per_paycheck_deduction,
)
from scripts.preflight_hw_check import run_preflight_checks
from scripts.seed_hw_data import seed_hw_database

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BenefitForge HW Eligibility & Test Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "BenefitForge HW Engine"}

@app.get("/api/participants")
def list_participants(db: Session = Depends(get_db)):
    participants = db.query(Participant).order_by(Participant.id).all()
    plans = db.query(BenefitPlan).order_by(BenefitPlan.id).all()
    result = []
    for p in participants:
        active_el = next((e for e in p.elections if e.status == "ACTIVE"), None)
        result.append({
            "id": p.id,
            "employee_code": p.employee_code,
            "full_name": p.full_name,
            "dob": str(p.dob),
            "employment_status": p.employment_status,
            "annual_salary": float(p.annual_salary),
            "scenario_tag": p.scenario_tag,
            "dependents": [
                {
                    "id": d.id,
                    "full_name": d.full_name,
                    "relationship_type": d.relationship_type,
                    "dob": str(d.dob),
                    "is_disabled": d.is_disabled
                }
                for d in p.dependents
            ],
            "active_election": {
                "plan_id": active_el.plan_id,
                "coverage_tier": active_el.coverage_tier,
                "per_paycheck_deduction": float(active_el.per_paycheck_deduction),
                "annual_hsa_contribution": float(active_el.annual_hsa_contribution),
                "effective_date": str(active_el.effective_date),
            } if active_el else None
        })
    return {
        "participants": result,
        "plans": [
            {
                "id": pl.id,
                "plan_code": pl.plan_code,
                "plan_name": pl.plan_name,
                "plan_type": pl.plan_type,
                "base_monthly_ee": float(pl.base_monthly_ee),
                "hsa_eligible": pl.hsa_eligible
            }
            for pl in plans
        ]
    }

@app.post("/api/enrollments/process-qle", response_model=QLEEnrollmentResponse, status_code=status.HTTP_200_OK)
def process_qle_enrollment(payload: QLEEnrollmentRequest, db: Session = Depends(get_db)):
    try:
        participant = db.query(Participant).filter(Participant.id == payload.participant_id).with_for_update().first()
        if not participant:
            raise HTTPException(status_code=404, detail=f"Participant ID {payload.participant_id} not found.")

        plan = db.query(BenefitPlan).filter(BenefitPlan.id == payload.plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Benefit Plan ID {payload.plan_id} not found.")

        current_election = (
            db.query(BenefitElection)
            .filter(BenefitElection.participant_id == participant.id, BenefitElection.status == "ACTIVE")
            .with_for_update()
            .first()
        )

        before_snapshot = ElectionSnapshot(
            coverage_tier=current_election.coverage_tier if current_election else None,
            per_paycheck_deduction=current_election.per_paycheck_deduction if current_election else None,
            annual_hsa_contribution=current_election.annual_hsa_contribution if current_election else None,
            effective_date=current_election.effective_date if current_election else None,
            status=current_election.status if current_election else "NONE",
        )

        if participant.employment_status != "ACTIVE_FT":
            raise HTTPException(
                status_code=400,
                detail=f"Participant employment status '{participant.employment_status}' is ineligible for active Medical/HDHP enrollment."
            )

        window_ok, window_msg = validate_qle_window(payload.qle_type, payload.event_date, payload.submitted_date)
        if not window_ok:
            raise HTTPException(status_code=400, detail=window_msg)

        for dep_id in payload.include_dependent_ids:
            dep = db.query(Dependent).filter(
                Dependent.id == dep_id,
                Dependent.participant_id == participant.id
            ).first()
            if not dep:
                raise HTTPException(status_code=404, detail=f"Dependent ID {dep_id} not associated with participant.")
            dep_ok, dep_msg = is_dependent_eligible(
                dep.relationship_type, dep.dob, payload.event_date, dep.is_disabled
            )
            if not dep_ok:
                raise HTTPException(status_code=400, detail=dep_msg)

        hsa_ok, hsa_msg = validate_hsa_statutory_limit(
            plan.hsa_eligible, payload.target_coverage_tier, payload.annual_hsa_contribution
        )
        if not hsa_ok:
            raise HTTPException(status_code=400, detail=hsa_msg)

        new_deduction = calculate_per_paycheck_deduction(
            Decimal(str(plan.base_monthly_ee)), payload.target_coverage_tier
        )

        if current_election:
            current_election.plan_id = plan.id
            current_election.coverage_tier = payload.target_coverage_tier
            current_election.per_paycheck_deduction = new_deduction
            current_election.annual_hsa_contribution = payload.annual_hsa_contribution
            current_election.effective_date = payload.event_date
            updated_election = current_election
        else:
            updated_election = BenefitElection(
                participant_id=participant.id,
                plan_id=plan.id,
                coverage_tier=payload.target_coverage_tier,
                per_paycheck_deduction=new_deduction,
                annual_hsa_contribution=payload.annual_hsa_contribution,
                effective_date=payload.event_date,
                status="ACTIVE"
            )
            db.add(updated_election)

        qle_log = QLEEvent(
            participant_id=participant.id,
            qle_type=payload.qle_type,
            event_date=payload.event_date,
            submitted_date=payload.submitted_date,
            status="APPROVED",
            reason="Verified all HW eligibility, dependent age-out, and HSA statutory rules."
        )
        db.add(qle_log)
        db.commit()
        db.refresh(updated_election)

        after_snapshot = ElectionSnapshot(
            coverage_tier=updated_election.coverage_tier,
            per_paycheck_deduction=updated_election.per_paycheck_deduction,
            annual_hsa_contribution=updated_election.annual_hsa_contribution,
            effective_date=updated_election.effective_date,
            status=updated_election.status,
        )

        return QLEEnrollmentResponse(
            qle_status="APPROVED",
            message=f"QLE ({payload.qle_type}) processed atomically. Per-paycheck deduction updated to ${new_deduction}.",
            participant_name=participant.full_name,
            before_state=before_snapshot,
            after_state=after_snapshot,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction error: {str(exc)}")

@app.post("/api/sandbox/seed")
def trigger_sandbox_seed(payload: SeedRequest):
    return seed_hw_database(payload.scenario)

@app.post("/api/sandbox/preflight")
def trigger_sandbox_preflight():
    return run_preflight_checks()

@app.post("/api/sandbox/run-tests")
def trigger_pytest_execution():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    proc = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=backend_dir, capture_output=True, text=True)
    return get_latest_reports(stdout=proc.stdout, returncode=proc.returncode)

@app.get("/api/sandbox/reports")
def get_latest_reports(stdout: str = "", returncode: int = 0):
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(backend_dir, "reports", "hw_verification_matrix.json")
    md_path = os.path.join(backend_dir, "reports", "hw_verification_matrix.md")
    csv_path = os.path.join(backend_dir, "reports", "hw_verification_matrix.csv")

    results, md_content, csv_content = [], "", ""
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f: results = json.load(f)
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f: md_content = f.read()
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f: csv_content = f.read()

    return {"returncode": returncode, "results": results, "markdown": md_content, "csv": csv_content, "stdout": stdout}
