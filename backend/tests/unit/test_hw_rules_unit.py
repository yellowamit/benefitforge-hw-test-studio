import pytest
from datetime import date
from decimal import Decimal
from app.services.eligibility import is_dependent_eligible, validate_qle_window, validate_hsa_statutory_limit, calculate_per_paycheck_deduction

@pytest.mark.req_id("HW-UNIT-01")
@pytest.mark.persona("Child Turning 26 Boundary")
def test_aca_dependent_age_out_exact_26th_birthday():
    dob = date(2000, 6, 15)
    assert is_dependent_eligible("CHILD", dob, date(2026, 6, 14))[0] is True
    ok_on_bday, msg = is_dependent_eligible("CHILD", dob, date(2026, 6, 15))
    assert ok_on_bday is False and "aged out" in msg

@pytest.mark.req_id("HW-UNIT-02")
@pytest.mark.persona("Disabled Adult Child")
def test_disabled_dependent_exempt_from_age_26_limit():
    assert is_dependent_eligible("CHILD", date(1995, 1, 10), date(2026, 6, 15), is_disabled=True)[0] is True

@pytest.mark.req_id("HW-UNIT-03")
@pytest.mark.persona("Mid-Year QLE Filer")
def test_qle_30_day_statutory_window_boundary():
    assert validate_qle_window("BIRTH", date(2026, 5, 1), date(2026, 5, 31))[0] is True
    assert validate_qle_window("BIRTH", date(2026, 5, 1), date(2026, 6, 1))[0] is False

@pytest.mark.req_id("HW-UNIT-04")
@pytest.mark.persona("HDHP Subscriber")
def test_hsa_statutory_limits_single_vs_family():
    assert validate_hsa_statutory_limit(True, "EE_ONLY", Decimal("4300.00"))[0] is True
    assert validate_hsa_statutory_limit(True, "EE_ONLY", Decimal("4300.01"))[0] is False
    assert validate_hsa_statutory_limit(True, "EE_FAMILY", Decimal("8550.00"))[0] is True

@pytest.mark.req_id("HW-UNIT-05")
@pytest.mark.persona("Payroll Proration Engine")
def test_per_paycheck_26_period_deduction_math():
    assert calculate_per_paycheck_deduction(Decimal("130.00"), "EE_FAMILY", pay_periods=26) == Decimal("156.00")
