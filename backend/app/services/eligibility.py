from datetime import date
from decimal import Decimal, ROUND_HALF_UP

TIER_MULTIPLIERS = {
    "EE_ONLY": Decimal("1.00"),
    "EE_CHILD": Decimal("1.65"),
    "EE_SPOUSE": Decimal("1.90"),
    "EE_FAMILY": Decimal("2.60"),
}

HSA_LIMIT_SINGLE = Decimal("4300.00")
HSA_LIMIT_FAMILY = Decimal("8550.00")

def calculate_age_on_date(dob: date, reference_date: date) -> int:
    age = reference_date.year - dob.year
    if (reference_date.month, reference_date.day) < (dob.month, dob.day):
        age -= 1
    return age

def is_dependent_eligible(relationship_type: str, dob: date, effective_date: date, is_disabled: bool = False) -> tuple[bool, str]:
    if relationship_type == "SPOUSE":
        return True, "Eligible spouse."
    if relationship_type == "CHILD":
        age = calculate_age_on_date(dob, effective_date)
        if age >= 26 and not is_disabled:
            return False, f"Dependent child aged out (Age {age} on {effective_date} >= ACA 26-year limit)."
        return True, f"Eligible child (Age {age})."
    return False, f"Unsupported relationship type: {relationship_type}"

def validate_qle_window(qle_type: str, event_date: date, submitted_date: date) -> tuple[bool, str]:
    if qle_type == "OPEN_ENROLLMENT":
        return True, "Open Enrollment period bypasses 30-day QLE check."
    days_elapsed = (submitted_date - event_date).days
    if days_elapsed < 0:
        return False, "QLE event_date cannot be in the future relative to submitted_date."
    if days_elapsed > 30:
        return False, f"QLE window expired: {days_elapsed} days elapsed since event_date (Max allowed: 30 days)."
    return True, f"QLE submitted within valid window ({days_elapsed} days)."

def validate_hsa_statutory_limit(hsa_eligible_plan: bool, coverage_tier: str, annual_hsa: Decimal) -> tuple[bool, str]:
    if annual_hsa == Decimal("0.00"):
        return True, "No HSA contribution elected."
    if not hsa_eligible_plan:
        return False, "Selected medical plan is not an HSA-qualified High Deductible Health Plan (HDHP)."
    limit = HSA_LIMIT_SINGLE if coverage_tier == "EE_ONLY" else HSA_LIMIT_FAMILY
    if annual_hsa > limit:
        return False, f"Annual HSA election (${annual_hsa}) exceeds statutory limit (${limit}) for tier {coverage_tier}."
    return True, "HSA contribution within statutory limits."

def calculate_per_paycheck_deduction(base_monthly_ee: Decimal, coverage_tier: str, pay_periods: int = 26) -> Decimal:
    multiplier = TIER_MULTIPLIERS.get(coverage_tier)
    if not multiplier:
        raise ValueError(f"Invalid coverage tier: {coverage_tier}")
    annual_ee_cost = base_monthly_ee * multiplier * Decimal("12")
    return (annual_ee_cost / Decimal(str(pay_periods))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
