# Dashboard Refactor Plan: Remove `CalculateKPIS`

## Overview

The dashboard currently uses the `CalculateKPIS` class (from `project/npda/kpi_class/kpis.py`)
to drive its PDU-level summary. The goal is to replace all `CalculateKPIS` usage in the
dashboard views with direct ORM queries, following the same pattern as the patient report
(`project/npda/general_functions/patient_report/queries.py`).

`CalculateKPIS` will remain untouched — it continues to drive national benchmarking and
other non-dashboard callers.

---

## Files in scope

| File | `CalculateKPIS` call sites | Notes |
|---|---|---|
| `views/dashboard/dashboard.py` | 2 | Simplest — Phase 1 |
| `views/dashboard/partials.py` | 5 (4 partials + `get_selected_chart_data`) | Phase 2 |
| `views/dashboard/patient_measurements.py` | 2 instances, ~7 KPI method calls | Most complex — Phase 3 |

---

## New functions to add to `queries.py`

All new functions follow the same conventions as the existing patient-report query functions:

- Accept `pdu` and `audit_period` as arguments (never `calculation_date` or `pz_code` directly)
- Use `build_base_queryset()` as the starting point
- Respect `audit_period.get_dataset_year()` for 2021 vs 2026 field differences
- Return plain Python values (counts, dicts) — no class state, no `KPIResult` objects

### Phase 1 — `dashboard.py`

| New function | Replaces | Return type |
|---|---|---|
| `count_eligible_patients(pdu, audit_period)` | `calculate_kpi_1_total_eligible()` | `int` — `type1_only=False` |
| `count_new_diagnoses_by_quarter(pdu, audit_period)` | `calculate_kpi_2_total_new_diagnoses_stratified_by_quarter()` | `dict[int, dict]` — identical shape `{q: {total_passed, total_eligible, pct}}` |

### Phase 2 — `partials.py`

| New function | Replaces | Return type |
|---|---|---|
| `count_hcl_use(pdu, audit_period)` | `calculate_kpi_24_hybrid_closed_loop_system()` | `tuple[int, int]` — `(passed, eligible)` |
| `count_pump_use(pdu, audit_period)` | `calculate_kpi_15_insulin_pump()` | `tuple[int, int]` — `(passed, eligible)` |
| `count_cgm_use(pdu, audit_period)` | `calculate_kpi_22_real_time_cgm_with_alarms()` | `tuple[int, int]` — `(passed, eligible)` |
| `count_admissions(pdu, audit_period)` | `calculate_kpi_46_number_of_admissions().total_passed` | `int` |
| `count_admissions_by_quarter(pdu, audit_period)` | `calculate_kpi_46_number_of_admissions_stratified_by_quarter()` | `dict[int, dict]` — same quarter shape |
| `count_service_transitions_by_quarter(pdu, audit_period)` | `calculate_total_service_transitions_to_adults_stratified_by_quarter()` | `dict[int, dict]` — same quarter shape |

Notes:
- `get_new_diagnoses_partial`, `get_transitioned_to_adult_service_partial`, and
  `get_moved_out_of_area_partial` already query `Submission.patients` directly — no
  `CalculateKPIS` involved, no changes needed.
- HCL, pump, and CGM are 2021/2026 dataset-year-aware via `annotate_treatment()`, which
  already handles both datasets.

### Phase 3 — `patient_measurements.py`

| New function | Replaces | Return type |
|---|---|---|
| `hba1c_stats_by_diabetes_type(pdu, audit_period)` | `calculate_kpi_hba1c_vals_stratified_by_diabetes_type()` | `dict` — same `{all, t1dm, t2dm, other}` shape with `mean_mmol_mol`, `mean_percent`, etc. |
| `dashboard_health_check_totals(pdu, audit_period)` | `patient_health_check_totals()` in `patient_measurements.py` | `dict` — same keys: `total_passed_bmi`, `total_eligible_bmi`, etc. |

Implementation notes:
- `dashboard_health_check_totals` uses `build_base_queryset(type1_only=True)` +
  `annotate_health_checks()`, then aggregates per-flag with `Count(..., filter=Q(...))`.
  This replaces the current approach of re-running individual KPI methods and intersecting
  querysets — one query instead of seven.
- `hba1c_stats_by_diabetes_type` queries `Visit` joined to `Patient`, filtered by
  `visit_date__range=audit_range`, groups by `patient__diabetes_type`, computes
  `Avg` and a median (see note below on median).
- HbA1c format normalisation (mmol/mol vs %) must be handled in the query layer, as
  `CalculateKPIS` currently does it in Python. The 2026 dataset drops `hba1c_format`;
  format is inferred from the value magnitude.

---

## Implementation order

1. **Phase 1** (`dashboard.py`) — smallest blast radius, establishes the pattern
2. **Phase 2** (`partials.py`) — one partial at a time, independently testable
3. **Phase 3** (`patient_measurements.py`) — HbA1c stats + health-check aggregation

---

## Template changes

None required. All new functions return the same dict/value shapes the existing templates
already consume.

---

## Test plan

### Test files affected

| Test file | Current state | Action |
|---|---|---|
| `tests/kpi_calculations/test_dashboard_kpi_calculations.py` | Calls `CalculateKPIS` methods directly | Rewrite to call new `queries.py` functions |
| `tests/view_tests/dashboard/test_partials.py` | HTTP-level; no `CalculateKPIS` directly | Minor: fix 2026-field assumptions in `VisitFactory` calls |
| `tests/view_tests/dashboard/test_patient_measurements.py` | HTTP-level; exercises `CalculateKPIS` indirectly | Fix missing `audit_period=` on `Submission`; fix 2026-field issues |
| `tests/view_tests/dashboard/test_patient_counts_by_diabetes_type.py` | No `CalculateKPIS` | No changes needed |

---

## 2026 dataset considerations

The `seed_audit_periods_fixture` seeds three periods: 2024–2025, 2025–2026, and 2026–2027.
Since today is April 2026, `AuditPeriod.objects.get_default_audit_period()` returns the
**2026–2027** period, so `audit_period.get_dataset_year()` returns `2026`.

### Field mapping changes (2021 → 2026)

| 2021 field | 2026 replacement | Dashboard relevance |
|---|---|---|
| `treatment` (combined regimen) | `insulin_regimen` | HCL / pump detection |
| `closed_loop_system` | `insulin_regimen == 5` (HCL) | HCL partial |
| `glucose_monitoring` | `cgm_use` | CGM partial |
| `hba1c_format` | removed (format inferred from value) | HbA1c stats |
| `smoking_status` | `smoking_vaping_status` | Not used in dashboard |

### Specific fixes required in existing tests

**`tests/view_tests/dashboard/test_partials.py`**
- `VisitFactory(hba1c_format=HBA1C_FORMATS[0][0], ...)` — remove `hba1c_format`
  (2021-only field; not meaningful in 2026 dataset and may cause unexpected behaviour)

**`tests/view_tests/dashboard/test_patient_measurements.py`**
- `Submission.objects.create(...)` is missing `audit_period=audit_period` — add it
- `VisitFactory(hba1c_format=HBA1C_FORMATS[0][0], ...)` — remove `hba1c_format`
- The eligibility logic for `total_eligible_blood_pressure`, `total_eligible_urinary_albumin`,
  `total_eligible_foot_exam` is unchanged (age-gated at 12); assertions remain valid

**`tests/kpi_calculations/test_dashboard_kpi_calculations.py`**
- Replace `CalculateKPIS` import and all method calls with calls to the new `queries.py`
  functions
- Existing tests use `AUDIT_START_DATE = date(2024, 4, 1)` (2021 dataset) — 2021-specific
  `Visit` fields (`treatment`, `glucose_monitoring`) remain correct for those tests
- Add new parallel tests using a 2026 `AuditPeriod` (`start_date >= 2026-04-01`) covering
  the same scenarios with 2026 fields (`insulin_regimen`, `cgm_use`)

### Test conventions to follow (per `AGENTS.md`)

- Required session fixtures: `seed_groups_fixture`, `seed_users_fixture`,
  `seed_audit_periods_fixture`, `client`
- Standard PDU: `ALDER_HEY_PZ_CODE` from `project.npda.tests.constants_for_tests`
- Use `submission.patients.add(patient)` in tests (not `submission.add_patient()`)
- `VisitFactory` has opinionated non-null defaults for `treatment`, `closed_loop_system`,
  `glucose_monitoring`; pass `None` explicitly when testing missing-data behaviour
- In 2026 tests: use `insulin_regimen` instead of `treatment`; use `cgm_use` instead of
  `glucose_monitoring`; omit `hba1c_format`

---

## Key constraints

- `CalculateKPIS` is **not deleted or modified** — other callers are unaffected
- All new query functions must be dataset-year-aware via `audit_period.get_dataset_year()`
- No template changes
- Run tests via `s/test` (Docker), never `pytest` directly on the host
