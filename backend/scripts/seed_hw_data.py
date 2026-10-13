import os, sys, argparse
from datetime import date
from decimal import Decimal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.models import Participant, Dependent, BenefitPlan, BenefitElection

def seed_hw_database(scenario: str = "all") -> dict:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        plans = [
            BenefitPlan(id=1, plan_code="MED-HDHP-2026", plan_name="Premier Consumer HDHP + HSA", plan_type="MEDICAL_HDHP", base_monthly_ee=Decimal("130.00"), base_monthly_er=Decimal("420.00"), hsa_eligible=True),
            BenefitPlan(id=2, plan_code="MED-PPO-2026", plan_name="Gold Co-Pay PPO Network", plan_type="MEDICAL_PPO", base_monthly_ee=Decimal("216.67"), base_monthly_er=Decimal("510.00"), hsa_eligible=False),
        ]
        db.add_all(plans)
        db.flush()

        all_participants = [
            (
                Participant(id=1, employee_code="EMP-1001", full_name="Ananya Sharma", dob=date(1992, 4, 15), hire_date=date(2022, 6, 1), employment_status="ACTIVE_FT", annual_salary=Decimal("95000.00"), scenario_tag="open_enrollment"),
                [
                    Dependent(id=1, participant_id=1, full_name="Rohan Sharma", relationship_type="SPOUSE", dob=date(1991, 8, 20), is_disabled=False),
                    Dependent(id=2, participant_id=1, full_name="Aarav Sharma", relationship_type="CHILD", dob=date(2026, 5, 10), is_disabled=False),
                ],
                BenefitElection(id=1, participant_id=1, plan_id=1, coverage_tier="EE_ONLY", per_paycheck_deduction=Decimal("60.00"), annual_hsa_contribution=Decimal("2400.00"), effective_date=date(2026, 1, 1), status="ACTIVE")
            ),
            (
                Participant(id=2, employee_code="EMP-1002", full_name="Vikram Patel (Part-Time)", dob=date(1995, 11, 2), hire_date=date(2024, 2, 15), employment_status="PART_TIME", annual_salary=Decimal("42000.00"), scenario_tag="open_enrollment"),
                [],
                None
            ),
            (
                Participant(id=3, employee_code="EMP-2001", full_name="Meera Krishnan (QLE Marriage/Birth)", dob=date(1989, 7, 19), hire_date=date(2021, 3, 10), employment_status="ACTIVE_FT", annual_salary=Decimal("112000.00"), scenario_tag="qle_life_events"),
                [Dependent(id=3, participant_id=3, full_name="Karthik Krishnan", relationship_type="SPOUSE", dob=date(1988, 12, 5), is_disabled=False)],
                BenefitElection(id=2, participant_id=3, plan_id=1, coverage_tier="EE_ONLY", per_paycheck_deduction=Decimal("60.00"), annual_hsa_contribution=Decimal("1500.00"), effective_date=date(2026, 1, 1), status="ACTIVE")
            ),
            (
                Participant(id=4, employee_code="EMP-3001", full_name="Rajesh Verma (Dependent Age-Out)", dob=date(1972, 1, 25), hire_date=date(2018, 9, 1), employment_status="ACTIVE_FT", annual_salary=Decimal("135000.00"), scenario_tag="dependent_age_out"),
                [
                    Dependent(id=4, participant_id=4, full_name="Kabir Verma (Age 26)", relationship_type="CHILD", dob=date(2000, 3, 1), is_disabled=False),
                    Dependent(id=5, participant_id=4, full_name="Diya Verma (Age 22)", relationship_type="CHILD", dob=date(2004, 7, 14), is_disabled=False),
                ],
                BenefitElection(id=3, participant_id=4, plan_id=2, coverage_tier="EE_CHILD", per_paycheck_deduction=Decimal("165.00"), annual_hsa_contribution=Decimal("0.00"), effective_date=date(2026, 1, 1), status="ACTIVE")
            ),
        ]

        p_cnt, d_cnt, e_cnt = 0, 0, 0
        for part, deps, election in all_participants:
            if scenario != "all" and part.scenario_tag != scenario:
                continue
            db.add(part)
            db.flush()
            p_cnt += 1
            for d in deps:
                db.add(d)
                d_cnt += 1
            if election:
                db.add(election)
                e_cnt += 1

        db.commit()
        return {"status": "SEEDED", "scenario": scenario, "participants_seeded": p_cnt, "dependents_seeded": d_cnt, "elections_seeded": e_cnt}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="all")
    args = parser.parse_args()
    print(seed_hw_database(args.scenario))
