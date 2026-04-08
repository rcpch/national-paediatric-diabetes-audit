# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.

---

## Running tests

**Always run tests inside the Docker container** using the `s/test` script.
Never call `pytest` directly on the host machine.

```bash
# Run a specific test
s/test project/npda/tests/view_tests/test_patient_report.py::test_name

# Run a whole test file
s/test project/npda/tests/view_tests/test_patient_report.py

# Run all tests
s/test
```

The script wraps: `docker compose run --rm django pytest -v $*`

---

## Project structure

### Patient report

The patient report is driven by its own dedicated query layer — **do not reach for the KPI class** when working on it.

| Path | Purpose |
|------|---------|
| `project/npda/general_functions/patient_report/queries.py` | All ORM queries that power the patient report (health checks, additional care processes, care at diagnosis, admissions, treatment, outcomes) |
| `project/npda/views/patient_report/patient_report.py` | View logic, context assembly, sorting, pagination, XLSX export |
| `project/npda/views/patient_report/patient_report.md` | Design intent, column definitions, edge cases and known shortcomings — **read before making changes** |
| `project/npda/templates/patient_report/` | Jinja/Django templates per category (e.g. `treatment_table_partial.html`) |

### KPI class

`project/npda/general_functions/calculate_kpis/` — for **PDU-level aggregates only**. Not used directly in the patient report row-level queries.

### Constants

`project/constants/` — canonical choice lists used across models, queries and templates.

| File | Contains |
|------|---------|
| `diabetes_treatment.py` | `TREATMENT_TYPES` |
| `glucose_monitoring_types.py` | `GLUCOSE_MONITORING_TYPES` |
| `closed_loop_types.py` | `CLOSED_LOOP_TYPES` |
| `diabetes_types.py` | `DIABETES_TYPES` |
| `smoking_status.py` | `SMOKING_STATUS` |
| `hba1c_format.py` | `HBA1C_FORMATS` |

---

## Test conventions

### Required fixtures

All view tests need these three session-scoped fixtures:

```python
def test_my_test(
    seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture, client
):
```

### Standard PDU

Use `ALDER_HEY_PZ_CODE` (imported from `project.npda.tests.constants_for_tests`) as the PDU in tests.

### Factories

| Factory | Import path |
|---------|-------------|
| `PatientFactory` | `project.npda.tests.factories.patient_factory` |
| `VisitFactory` | `project.npda.tests.factories.visit_factory` |

**`VisitFactory` has opinionated non-null defaults** for `treatment`, `closed_loop_system` and `glucose_monitoring`. Pass `None` explicitly when testing missing-data behaviour:

```python
VisitFactory(patient=patient, visit_date=visit_date, treatment=None)
```

### Authentication

```python
from project.npda.tests.utils import login_and_verify_user

user = NPDAUser.objects.filter(
    organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    role=test_user_audit_centre_editor_data.role,
).first()
client = login_and_verify_user(client, user)
```

### Submission wiring

Patients must be added to a `Submission` to appear in patient report queries:

```python
submission = Submission.objects.create(
    paediatric_diabetes_unit=user.organisation_employers.first(),
    audit_year=audit_period.start_date.year,
    audit_period=audit_period,
    submission_date=audit_period.start_date,
    submission_by=user,
    submission_active=True,
)
submission.patients.add(patient)
```

### Patient report response shape

The patient report view returns patients as a list of dicts in `response.context["patients"]`.
Keys match the annotation names in `queries.py` (e.g. `"treatment_regimen"`, `"glucose_monitoring"`, `"hcl"`), not the model field names.

---

## `s/` scripts reference

All convenience scripts live in `s/`. They must be run from the repo root.

| Script | What it does |
|--------|-------------|
| `s/up` | Start all Docker Compose services |
| `s/down` | Stop all services |
| `s/rebuild` | Remove containers/images then bring up fresh |
| `s/local-clean-reset` | Nuclear reset: removes volumes and images, then `s/up` |
| `s/start-dev` | Run migrations, seed data, start Django dev server on port 8008 |
| `s/watch-tailwind` | Compile Tailwind CSS in watch mode |
| `s/django-shell` | Open Django shell inside the running container |
| `s/test` | Run pytest in a one-shot container (passes all args to pytest) |
| `s/lint` | Run ruff formatter + linter in fix mode |
| `s/lint --check` | Lint check only (used in CI, exits non-zero if unclean) |
| `s/psql` | Connect to Postgres (local or Azure, see script for options) |
| `s/create-superuser` | Create a Django superuser inside the container |
| `s/start-celery-dev` | Start Celery worker for local development |

---

## Linting / formatting

The project uses **ruff** for both formatting and linting.

```bash
s/lint          # fix in place
s/lint --check  # CI mode
```

---

## Datasets

There are two datasets: **2021** and **2026**. The dataset year is derived from the audit period and controls which CSV columns are accepted on upload, which field labels are shown in the UI, and which model fields are active.

### How the dataset year is resolved

`AuditPeriod.get_dataset_year()` returns `2026` if `start_date >= 2026-04-01`, otherwise `2021`. Everything downstream uses this single method — do not hardcode a year.

### Where the dataset year is used

| Location | Purpose |
|----------|---------|
| `project/npda/general_functions/headings.py` | `get_field_heading(field_name, dataset_year)` — returns the year-appropriate CSV column heading for a given model field |
| `project/constants/csv_headings.py` | `ALL_HEADINGS` — master list of every field with a `dataset_years` list indicating which datasets include it |
| `project/npda/general_functions/csv/csv_upload.py` | Infers `dataset_year` from the submission's audit period (or from column sniffing) before parsing |
| `project/npda/models/patient.py` | `Patient.get_field_label()`, `get_sex_label()` etc. delegate to `get_field_heading` |
| `project/npda/models/visit.py` | `Visit.get_field_label()` delegates to `get_field_heading` |
| `project/npda/forms/patient_form.py` / `visit_form.py` | Form field labels are resolved via `get_field_heading` at form instantiation |

### Key differences between datasets

**Patient model — 2026 only fields:**
- `sex` heading changes from "Stated gender" → "Sex assigned at birth"
- `adhd_asd_status` — ADHD/ASD diagnosis
- `learning_disability_status` — learning disability diagnosis
- `immunotherapy_received` / `immunotherapy_date` — immunotherapy for stage 3 T1DM

**Visit model — 2021 only fields (replaced in 2026):**
- `treatment` — combined treatment regimen (replaced by `insulin_regimen` + `non_insulin_medication` + `dietary_lifestyle_modification`)
- `closed_loop_system` — closed loop flag (still present but linked to `treatment`; logic changes)
- `glucose_monitoring` — other glucose monitoring method (replaced by `cgm_use`)
- `hba1c_format` — HbA1c format field (removed in 2026; format is inferred)
- `smoking_status` — "Does the patient smoke?" (replaced by `smoking_vaping_status`)

**Visit model — 2026 only fields:**
- `insulin_regimen` — insulin type at time of visit
- `non_insulin_medication` — other blood glucose lowering medication
- `dietary_lifestyle_modification` — lifestyle/dietary modification recommended
- `cgm_use` — CGM use at time of visit
- `smoking_vaping_status` — "Does the patient smoke and/or vape"
- `blood_gas_ph` / `blood_gas_bicarbonate` — DKA admission blood gas values
- `psychological_support_outcome` — whether patient was offered additional mental health appointment

### Adding new fields

When adding a field that is dataset-year-specific:
1. Add the model field to `Patient` or `Visit` (nullable)
2. Add an entry to `ALL_HEADINGS` in `project/constants/csv_headings.py` with the correct `dataset_years` list
3. Add the heading to `PATIENT_FIELD_HEADINGS_202x` / `VISIT_FIELD_HEADINGS_202x` in `project/npda/general_functions/headings.py`
4. The form, CSV upload, and display layers will pick it up automatically via `get_field_heading`

---

## Notes on Jersey (PZ248)

Patients at the Jersey PDU (`pz_code == "PZ248"`) use `unique_reference_number` as their identifier instead of `nhs_number`. The helper `_patient_identifier_field(pdu)` in `queries.py` handles this. Tests that check `patient_identifier` should be aware of this distinction.
