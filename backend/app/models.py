from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    hire_date = Column(Date, nullable=False)
    employment_status = Column(String(20), nullable=False)
    annual_salary = Column(Numeric(12, 2), nullable=False)
    scenario_tag = Column(String(40), nullable=False, default="open_enrollment")

    dependents = relationship("Dependent", back_populates="participant", cascade="all, delete-orphan")
    elections = relationship("BenefitElection", back_populates="participant", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("annual_salary >= 0", name="chk_participant_salary_positive"),
    )

class Dependent(Base):
    __tablename__ = "dependents"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(100), nullable=False)
    relationship_type = Column(String(20), nullable=False)
    dob = Column(Date, nullable=False)
    is_disabled = Column(Boolean, default=False, nullable=False)

    participant = relationship("Participant", back_populates="dependents")

class BenefitPlan(Base):
    __tablename__ = "benefit_plans"
    id = Column(Integer, primary_key=True, index=True)
    plan_code = Column(String(30), unique=True, nullable=False, index=True)
    plan_name = Column(String(100), nullable=False)
    plan_type = Column(String(20), nullable=False)
    base_monthly_ee = Column(Numeric(10, 2), nullable=False)
    base_monthly_er = Column(Numeric(10, 2), nullable=False)
    hsa_eligible = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        CheckConstraint("base_monthly_ee >= 0", name="chk_plan_ee_cost_non_negative"),
    )

class BenefitElection(Base):
    __tablename__ = "benefit_elections"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("benefit_plans.id", ondelete="RESTRICT"), nullable=False)
    coverage_tier = Column(String(25), nullable=False)
    per_paycheck_deduction = Column(Numeric(10, 2), nullable=False)
    annual_hsa_contribution = Column(Numeric(10, 2), nullable=False, default=0.00)
    effective_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")

    participant = relationship("Participant", back_populates="elections")
    plan = relationship("BenefitPlan")

    __table_args__ = (
        CheckConstraint("per_paycheck_deduction >= 0", name="chk_election_deduction_non_negative"),
        CheckConstraint("annual_hsa_contribution >= 0 AND annual_hsa_contribution <= 8550.00", name="chk_hsa_statutory_max"),
    )

class QLEEvent(Base):
    __tablename__ = "qle_events"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    qle_type = Column(String(30), nullable=False)
    event_date = Column(Date, nullable=False)
    submitted_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=True)
