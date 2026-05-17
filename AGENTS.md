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

| Path                                                       | Purpose                                                                                                                                                                                                  |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `project/npda/general_functions/patient_report/queries.py` | All ORM queries that power the patient report **and the dashboard** (health checks, additional care processes, care at diagnosis, admissions, treatment, outcomes, plus all dashboard summary functions) |
| `project/npda/views/patient_report/patient_report.py`      | View logic, context assembly, sorting, pagination, XLSX export                                                                                                                                           |
| `project/npda/views/patient_report/patient_report.md`      | Design intent, column definitions, edge cases, known shortcomings, and **the authoritative 2021/2026 field mapping per category — read this before touching any patient report query**                   |
| `project/npda/templates/patient_report/`                   | Jinja/Django templates per category (e.g. `treatment_table_partial.html`)                                                                                                                                |

When working on patient report queries, always check `patient_report.md` for the correct field to use for the active dataset year. Several fields changed or were added in 2026 (e.g. `treatment` → `insulin_regimen`, `glucose_monitoring` → `cgm_use`, `smoking_status` → `smoking_vaping_status`). The `audit_period.get_dataset_year()` method is the single source of truth — never hardcode a year.

### Dashboard

The dashboard views also use `queries.py` directly — **do not reach for the KPI class** when working on dashboard code.

| Path                                                   | Purpose                                                                             |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `project/npda/views/dashboard/dashboard.py`            | Main dashboard view — eligible patient count and new-diagnoses quarter chart        |
| `project/npda/views/dashboard/partials.py`             | HTMX partials — HCL, pump, CGM, admissions, service transitions, map                |
| `project/npda/views/dashboard/patient_measurements.py` | Measurements card — HbA1c stats by diabetes type, health-check pass/eligible counts |
| `project/npda/templates/dashboard/`                    | Dashboard templates                                                                 |

**Dashboard query functions in `queries.py`** (all accept `pdu, audit_period`):

| Function                               | Returns           | Notes                                                                                                                      |
| -------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `count_eligible_patients`              | `int`             | All diabetes types, complete-year filter                                                                                   |
| `count_new_diagnoses_by_quarter`       | `dict[int, dict]` | `{q: {total_passed, total_eligible, pct}}`                                                                                 |
| `count_hcl_use`                        | `tuple[int, int]` | `(passed, eligible)` — 2021/2026 aware                                                                                     |
| `count_pump_use`                       | `tuple[int, int]` | `(passed, eligible)` — 2021/2026 aware                                                                                     |
| `count_cgm_use`                        | `tuple[int, int]` | `(passed, eligible)` — 2021/2026 aware                                                                                     |
| `count_admissions`                     | `int`             | Total admissions count                                                                                                     |
| `count_admissions_by_quarter`          | `dict[int, dict]` | Quarter-stratified admissions                                                                                              |
| `count_service_transitions_by_quarter` | `dict[int, dict]` | Quarter-stratified adult-service transitions                                                                               |
| `hba1c_stats_by_diabetes_type`         | `dict`            | `{all, t1dm, t2dm, other}` each with `mean_mmol_mol`, `median_mmol_mol`, `mean_percent`, `median_percent`; 2021/2026 aware |
| `dashboard_health_check_totals`        | `dict`            | `total_passed_*` / `total_eligible_*` for BMI, thyroid, BP, urinary albumin, foot exam; single aggregation query           |

All dashboard functions use `build_base_queryset()` as their base and respect `audit_period.get_dataset_year()`. They return plain Python values — no `KPIResult` objects.

### Dashboard map component (IMD)

The dashboard IMD map in `project/npda/templates/dashboard/map_chart_partial.html` uses the browser bundle from `@rcpch/imd-map`.

- Current bundle version: `0.5.1`
- Script URL:
  `https://cdn.jsdelivr.net/npm/@rcpch/imd-map@0.5.1/dist/umd/rcpch-imd-map.min.js`
- Current SRI:
  `sha512-eL1iCgZ8KVnELAEum+mIwBG58FdZPUYJ/8B1eUHOGc0AQAdVIQoZSc6myiygjgLKZrB0I5XbU+ZDQpYb66EJkw==`

Tile auth is now configured via map options (query-string auth), not request headers.

- Token source: `settings.RCPCH_CENSUS_PLATFORM_TOKEN`
- Passed from view context in `project/npda/views/dashboard/partials.py`
- Consumed in JS as:

```javascript
RcpchImdMap.createImdMap({
  container: container,
  tilesBaseUrl: tilesBaseUrl,
  tilesApiKey: window.RCPCH_CENSUS_PLATFORM_TOKEN || undefined,
  tilesApiKeyParam: "Subscription-Key",
});
```

Keep the API key plumbing aligned with `project/npda/general_functions/index_multiple_deprivation.py`, which uses the same token setting for server-side deprivation requests.

### KPI class

`project/npda/general_functions/calculate_kpis/` — for **national benchmarking aggregates only**. Not used directly in patient report or dashboard views.

### Core models

| Model               | Path                                       | Notes                                                                                                                                                                                                                                 |
| ------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Patient`           | `project/npda/models/patient.py`           | `nhs_number` and `unique_reference_number` are both `unique=False` at the DB level — uniqueness within a PDU's submission is enforced by `Submission.add_patient()`, not a DB constraint                                              |
| `Submission`        | `project/npda/models/submission.py`        | One active submission per PDU per audit period. Use `Submission.objects.get_submission_for_request(pdu, audit_period)` to fetch it. **Always use `submission.add_patient(patient)` in production code** (see Submission wiring below) |
| `PatientSubmission` | `project/npda/models/patientsubmission.py` | Through-table for the `Submission ↔ Patient` M2M. No custom validation — uniqueness lives on `Submission.add_patient()`                                                                                                               |
| `Transfer`          | `project/npda/models/transfer.py`          | One `Transfer` per `Patient`, recording their current PDU. Created alongside the `Patient` in `PatientCreateView.form_valid()`                                                                                                        |
| `Visit`             | `project/npda/models/visit.py`             | FK to `Patient`. Many visits per patient per audit period                                                                                                                                                                             |
| `AuditPeriod`       | `project/npda/models/audit_period.py`      | Use `AuditPeriod.objects.get_default_audit_period()` in tests. `audit_period.get_dataset_year()` is the single source of truth for 2021 vs 2026                                                                                       |

### Constants

`project/constants/` — canonical choice lists used across models, queries and templates.

| File                          | Contains                   |
| ----------------------------- | -------------------------- |
| `diabetes_treatment.py`       | `TREATMENT_TYPES`          |
| `glucose_monitoring_types.py` | `GLUCOSE_MONITORING_TYPES` |
| `closed_loop_types.py`        | `CLOSED_LOOP_TYPES`        |
| `diabetes_types.py`           | `DIABETES_TYPES`           |
| `smoking_status.py`           | `SMOKING_STATUS`           |
| `hba1c_format.py`             | `HBA1C_FORMATS`            |

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

| Factory          | Import path                                    |
| ---------------- | ---------------------------------------------- |
| `PatientFactory` | `project.npda.tests.factories.patient_factory` |
| `VisitFactory`   | `project.npda.tests.factories.visit_factory`   |

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

Patients must be added to a `Submission` to appear in patient report queries.

**In tests** use `submission.patients.add(patient)` directly — the uniqueness guard is not needed in test setup and bypassing it keeps fixtures simple:

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

**In production code** (views, management commands, etc.) always use `submission.add_patient(patient)` instead of the bare `patients.add()`. This method enforces a PDU-scoped uniqueness rule: a patient with the same NHS number (or Unique Reference Number for Jersey patients) cannot appear more than once across any active submissions for the _same PDU_ in the same audit period. The same identifier is allowed in a different PDU's submission (e.g. after a cross-PDU transfer). A `ValidationError` is raised on violation.

```python
# Raises ValidationError if NHS/URN already in an active submission for this PDU
submission.add_patient(patient)
```

### Patient report response shape

The patient report view returns patients as a list of dicts in `response.context["patients"]`.
Keys match the annotation names in `queries.py` (e.g. `"treatment_regimen"`, `"glucose_monitoring"`, `"hcl"`), not the model field names.

---

## `s/` scripts reference

All convenience scripts live in `s/`. They must be run from the repo root.

| Script                | What it does                                                    |
| --------------------- | --------------------------------------------------------------- |
| `s/up`                | Start all Docker Compose services                               |
| `s/down`              | Stop all services                                               |
| `s/rebuild`           | Remove containers/images then bring up fresh                    |
| `s/local-clean-reset` | Nuclear reset: removes volumes and images, then `s/up`          |
| `s/start-dev`         | Run migrations, seed data, start Django dev server on port 8008 |
| `s/watch-tailwind`    | Compile Tailwind CSS in watch mode                              |
| `s/django-shell`      | Open Django shell inside the running container                  |
| `s/test`              | Run pytest in a one-shot container (passes all args to pytest)  |
| `s/lint`              | Run ruff formatter + linter in fix mode                         |
| `s/lint --check`      | Lint check only (used in CI, exits non-zero if unclean)         |
| `s/psql`              | Connect to Postgres (local or Azure, see script for options)    |
| `s/create-superuser`  | Create a Django superuser inside the container                  |
| `s/start-celery-dev`  | Start Celery worker for local development                       |

### IMD recalculation command (basic use)

Use the management command below to recalculate `index_of_multiple_deprivation_quintile`
for patients in an audit period using postcode country and audit-period-aware England year mapping.

```bash
# Dry run against default audit period
python manage.py recalculate_imd --dry-run

# Run for a specific audit period
python manage.py recalculate_imd --audit-period 2026-2027
```

For full options and examples, see `documentation/docs/developer/useful-scripts.md`.

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

| Location                                               | Purpose                                                                                                                 |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `project/npda/general_functions/headings.py`           | `get_field_heading(field_name, dataset_year)` — returns the year-appropriate CSV column heading for a given model field |
| `project/constants/csv_headings.py`                    | `ALL_HEADINGS` — master list of every field with a `dataset_years` list indicating which datasets include it            |
| `project/npda/general_functions/csv/csv_upload.py`     | Infers `dataset_year` from the submission's audit period (or from column sniffing) before parsing                       |
| `project/npda/models/patient.py`                       | `Patient.get_field_label()`, `get_sex_label()` etc. delegate to `get_field_heading`                                     |
| `project/npda/models/visit.py`                         | `Visit.get_field_label()` delegates to `get_field_heading`                                                              |
| `project/npda/forms/patient_form.py` / `visit_form.py` | Form field labels are resolved via `get_field_heading` at form instantiation                                            |

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

---

## CSV pipeline — `csv_parse` and `csv_headings`

### Key files

| File                                              | Purpose                                                                                                                |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `project/constants/csv_headings.py`               | `ALL_HEADINGS` master list + helper functions                                                                          |
| `project/npda/general_functions/csv/csv_parse.py` | Reads a CSV file into a pandas DataFrame, normalises headings, detects the unique identifier, and records parse errors |
| `project/npda/general_functions/csv/csv_clean.py` | Converts date strings to `pd.Timestamp`, cleans sex/ethnicity/measurement columns                                      |

### `ALL_HEADINGS` structure

Each entry in `ALL_HEADINGS` is a dict with:

```python
{
    "heading": "<canonical CSV column name>",
    "model_field": "<Django model field name>",
    "model": "Patient" | "Visit" | "Transfer",  # absent for PDU Number
    "data_type": "string" | "date" | "int64" | "float64",
    "dataset_years": [2021] | [2026] | [2021, 2026],
    "alternative_headings": [...],  # optional
}
```

Fields shared between both years have `dataset_years: [2021, 2026]`. Year-specific fields have only their year in the list. When a heading _name_ changes between years, two separate entries share the same `model_field` (the deduplication in `get_csv_heading_objects` ensures each year's canonical heading is returned once).

### Helper functions in `csv_headings.py`

| Function                                                                                  | Returns                                                                                                       |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `get_csv_heading_objects(dataset_year)`                                                   | Tuple of heading dicts for the given year (deduped by `model_field`)                                          |
| `get_csv_heading_objects_for_year_and_unique_identifier(dataset_year, unique_identifier)` | Like above but also prepends the correct patient identifier heading (England NHS number, Jersey URN, or both) |
| `get_all_dates(dataset_year)`                                                             | List of CSV column _headings_ whose `data_type == "date"` for the given year                                  |
| `csv_definition_for(model_field_or_column, dataset_year)`                                 | Single heading dict for a model field name or column heading                                                  |

### `csv_parse` flow

1. Reads the CSV with `pd.read_csv` (UTF-8, fallback ISO-8859-1).
2. Strips column whitespace and quotes; renames alternative headings to canonical ones.
3. Detects the unique-identifier column (NHS Number / URN) — raises if neither or both present.
4. Validates no row is missing its identifier.
5. Detects and records duplicate columns (e.g. `"XYZ.1"`).
6. Parses each column to its declared `data_type` using `pd.to_numeric` / `pd.to_datetime` etc., recording per-row parse errors in `errors_to_return`.
7. Returns a `ParsedCSVFile` dataclass containing the DataFrame (`df`), identifier column, missing/additional/duplicate columns, and `errors_to_return`.

### `csv_clean` flow

Called inside `csv_upload` after `csv_parse`. Applies:

- `pd.to_datetime` (day-first, mixed format) to all date columns returned by `get_all_dates(dataset_year)`.
- Custom cleaners for `sex`, `ethnicity`, `height`, `weight`.
- Whitespace stripping across all string/object columns.

---

## CSV pipeline — `csv_upload`

### Overview

`csv_upload` is an `async` function that processes an already-parsed-and-cleaned pandas DataFrame and persists the rows as `Patient`, `Transfer`, and `Visit` records. It is parallelised with an `asyncio.TaskGroup` (up to 5 concurrent patients).

### Key file

`project/npda/general_functions/csv/csv_upload.py`

### High-level flow

```
csv_upload(dataframe, errors_to_return, csv_file_name, submission)
  │
  ├─ Infer dataset_year from submission.audit_period.get_dataset_year()
  │    (sniff 2026-only headings in the dataframe to override if needed)
  │
  ├─ Build CSV_HEADINGS for this year + PDU identifier via
  │    get_csv_heading_objects_for_year_and_unique_identifier()
  │
  ├─ csv_clean(dataframe, dataset_year)  — normalise dates, measurements, etc.
  │
  ├─ Group rows by patient identifier (NHS Number or URN)
  │
  └─ For each patient group (in parallel, semaphore=5):
       │
       ├─ merge_rows_for_patient()  — resolve conflicts across multiple rows
       │                              (e.g. conflicting date-of-birth, diagnosis date,
       │                               reason_leaving_service)
       │
       ├─ validate_patient_using_form(first_row)
       │    row_to_dict(row, Patient) | row_to_dict(row, Transfer)
       │    → PatientForm(fields)  — validates patient + transfer fields together
       │    → validate_patient_async()  — external postcode / GP lookup
       │
       ├─ For each visit row:
       │    validate_visit_using_form(row)
       │    → VisitForm(fields)
       │    → validate_visit_async()  — external BMI centile lookup
       │
       ├─ get_valid_transfer_fields(first_row, patient_form)
       │    row_to_dict(row, Transfer)
       │    Nulls out any Transfer field that has an "invalid" / "invalid_choice"
       │    validation error on the PatientForm
       │
       └─ save_patient_and_transfer(patient_form, transfer_fields)
            patient_form.save(commit=False) + patient.asave()
            Transfer.objects.acreate(**transfer_fields)
            submission.patients.aadd(patient)
            → save_visits(patient, visit_forms)
```

### `row_to_dict(row, model)`

Iterates `CSV_HEADINGS` filtering by `model`. For each matching entry it:

1. Looks up the model field definition via `model._meta.get_field(model_field_name)`.
2. Reads `row[entry["heading"]]`.
3. Converts the value via `csv_value_to_model_value()` — handles NaN → None, `pd.Timestamp` → `datetime.date`, numpy scalars → Python scalars, integer-valued floats → int.

### Transfer field handling

`date_leaving_service` and `reason_leaving_service` live on the `Transfer` model but are also declared on `PatientForm` so they can be validated together with patient-level cross-field rules (see `PatientForm.clean()`). The save path is:

1. Both fields enter `validate_patient_using_form` via `row_to_dict(row, Transfer)`.
2. They are individually cleaned by `PatientForm.clean_date_leaving_service` / `clean_reason_leaving_service`.
3. Cross-field rules in `PatientForm.clean()` ensure neither is supplied without the other.
4. `get_valid_transfer_fields` calls `row_to_dict(row, Transfer)` again and nulls any field that has an "invalid" / "invalid_choice" form error.
5. Both fields are passed to `Transfer.objects.acreate(**transfer_fields)`.

### Error accumulation

Errors are accumulated in `errors_to_return: dict[row_index, dict[field_name, list[str]]]` and come from two sources: `csv_parse` (type-parse errors recorded at read time) and the Django forms (validation errors recorded at upload time). Both sets are merged before being stored on `submission.errors` as JSON.
