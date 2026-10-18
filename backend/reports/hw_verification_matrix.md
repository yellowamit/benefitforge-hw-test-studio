# BenefitForge — Health & Welfare Verification Matrix
**Total:** 9 | **Passed:** 9

| Req ID     | Persona                           | Suite            | Test Case                                                     | Status   |   Latency (ms) |
|------------|-----------------------------------|------------------|---------------------------------------------------------------|----------|----------------|
| HW-INT-01  | Ananya Sharma (EMP-1001)          | Integration (DB) | test_valid_birth_qle_updates_tier_and_payroll_deduction_in_db | PASSED   |          41.25 |
| HW-INT-02  | Meera Krishnan (EMP-2001)         | Integration (DB) | test_expired_qle_over_30_days_rolls_back_db_state             | PASSED   |           9.19 |
| HW-INT-03  | Rajesh Verma (EMP-3001)           | Integration (DB) | test_reject_aged_out_26yo_dependent_preserves_db              | PASSED   |          11.18 |
| HW-INT-04  | Vikram Patel (EMP-1002 Part-Time) | Integration (DB) | test_part_time_employee_blocked_from_hdhp_enrollment          | PASSED   |           9.37 |
| HW-UNIT-01 | Child Turning 26 Boundary         | Unit             | test_aca_dependent_age_out_exact_26th_birthday                | PASSED   |           0.33 |
| HW-UNIT-02 | Disabled Adult Child              | Unit             | test_disabled_dependent_exempt_from_age_26_limit              | PASSED   |           0.22 |
| HW-UNIT-03 | Mid-Year QLE Filer                | Unit             | test_qle_30_day_statutory_window_boundary                     | PASSED   |           0.32 |
| HW-UNIT-04 | HDHP Subscriber                   | Unit             | test_hsa_statutory_limits_single_vs_family                    | PASSED   |           0.27 |
| HW-UNIT-05 | Payroll Proration Engine          | Unit             | test_per_paycheck_26_period_deduction_math                    | PASSED   |           0.46 |
