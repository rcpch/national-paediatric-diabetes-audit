# The Patient Report

## High Level View of Structure

The patient report is a high level summary of compliance with key KPIs in the National Paediatric Diabetes Audit. Note it only applies to children with T1 diabetes.

It should be downloadable as a PDF/xlsx (see issue #1238)

It contains a dashboard of compliance for a given Paediatric Diabetes Unit against key audit measures in the following categories:

- Health Checks
- Additional Care Processes
- Care at Diagnosis
- Admissions
- Treatment
- Outcomes

Each category lists all patients in a PDU as a table with flags (complete/incomplete/not required/incomplete year of care) against the individual measures in that category, each as a column. The column header has a facet for total numbers completed.

Each row represents an individual patient, with the first column their unique identifier.

The patients are sorted with those with with incomplete measures showing first in the list, so that users can identify patients that still need care processes improving. It is possible to resort the patients in descending or ascending order by clicking on a given column header. The user can click through from the patient identifier (NHS number or Unique Reference Number) to the patient record [see issue #1310].

An incomplete year of care can occur in two situations:

- The patient was diagnosed within the current audit year (diagnosis_date on the Patient model)
- The patient transferred out of this PDU in the current audit year (date_leaving_service is set on the Transfer model associated with the patient)

The columns per category are as follows:

### Health Checks

- NHS Number
- HBA1c
- BMI
- Thyroid Screen
- Blood Pressure
- Urinary Albumin
- Foot Exam
- Total
- Eye Screen

Note the **Total** refers to children who have completed all checks in the audit period. The rules for this are as follows:
Patients < 12 years => 3 expected health checks (HbA1c, BMI, Thyroid)
Patients >= 12 years => 6 expected health checks (HbA1c, BMI, Thyroid, BP, Urinary Albumin, Foot Exam)

Note: Excludes Retinal Screening, which only needs to be completed every 2 years [see issue #1296].

Note retinal screening is counted only every 2 years (see issue #1285) and only apply to patients over 12y who have more than 1 of diabetes.

**Dataset field mapping — unchanged between 2021 and 2026:**

| Column | Model field | Notes |
|--------|-------------|-------|
| HbA1c | `hba1c` + `hba1c_date` | Both datasets |
| BMI | `bmi` + `height_weight_observation_date` | Both datasets |
| Thyroid screen | `thyroid_function_date` | Both datasets |
| Blood pressure | `systolic_blood_pressure` + `blood_pressure_observation_date` | Both datasets; ≥12 only |
| Urinary albumin | `albumin_creatinine_ratio` + `albumin_creatinine_ratio_date` | Both datasets; ≥12 only |
| Foot exam | `foot_examination_observation_date` | Both datasets; ≥12 only |
| Eye screen | `retinal_screening_observation_date` + `retinal_screening_result` | Both datasets; ≥12, dx >1y, biannual |

### Additional Care Processes

- NHS Number
- HBA1C 4+
- Psychological assessment
- Smoking status screened
- Referral to smoking cessation service
- Additional dietetic appointment offered
- Patients attending additional dietetic appointment
- Influenza immunisation recommended
- Sick day rules advice

These measures are all scored with flags, as in the Health Checks category. HbA1c 4+ reflects if a patient has had 4 HbA1c values (and associated date) within the audit period to get a complete. Incomplete is otherwise scored unless the patient has an incomplete year of care. Note that smoking status screened and referral to smoking status are only scored in children >= 12y. Smoking status is incomplete if they are scored as a smoker but a referral date is not provided.

**Dataset field mapping:**

| Column | 2021 field | 2026 field | Notes |
|--------|------------|------------|-------|
| HbA1c 4+ | `hba1c` + `hba1c_date` | same | Both datasets |
| Psychological assessment | `psychological_screening_assessment_date` | same | Both datasets |
| Smoking status screened | `smoking_status` (1=non-smoker, 2=smoker) | `smoking_vaping_status` (same integer values) | ≥12 only |
| Referral to smoking cessation | `smoking_cessation_referral_date` (when smoker) | same field, same logic | ≥12, smokers only |
| Additional dietetic appt offered | `dietician_additional_appointment_offered` | same | Both datasets |
| Patients attending additional dietetic appt | `dietician_additional_appointment_date` | same | Both datasets |
| Influenza immunisation | `flu_immunisation_recommended_date` | same | Both datasets |
| Sick day rules advice | `sick_day_rules_training_date` | same | Both datasets |
| Psychological support outcome | *(absent)* | `psychological_support_outcome` | 2026 only — new column |

### Care at Diagnosis

- NHS Number
- Date of Diagnosis
- Carbohydrate counting education
- Date of Diagnosis + 14 days
- Coeliac disease screening
- Thyroid disease screening
- Date of Diagnosis + 90 days

These items are scored using flags as with Health Checks.

Patients must be screened for coeliac disease and thyroid function within 90 days of diagnosis (to include the day of diagnosis) to score as complete. If there is no date within this audit period of a child diagnosed within the last 90 days (and that did not have the check in the previous audit period if diagnosed then and still within 90 days - see issue #1327), they are marked as incomplete. It they have had diabetes for more than a year they are marked as not required, and also if they have an incomplete year of care.

The same methodology applies to carbohydrate counting, though the threshold is 14 days.

- [ ] It is preferable for there to be an extra column here with a countdown in days til this measure is due. (see issue #1301)
- [ ] It is also preferable that carbohydrate counting, coeliac and thyroid screening that are incomplete (that is where there is a date but not within the time frame) are rather labelled as 'missed' than 'incomplete'. (see issue #1301)

**Dataset field mapping — unchanged between 2021 and 2026:**

| Column | Model field | Notes |
|--------|-------------|-------|
| Carbohydrate counting | `carbohydrate_counting_level_three_education_date` | Both datasets; within 14 days of diagnosis |
| Coeliac screening | `coeliac_screen_date` | Both datasets; within 90 days of diagnosis |
| Thyroid screening | `thyroid_function_date` | Both datasets; within 90 days of diagnosis |

### Admissions

- NHS Number
- Mean HbA1c mmol/mol (%)
- Median HbA1c mmol/mol (%)
- Number of admissions
- Number of DKA admissions

This category relates only to patients that have had a hospital admission during the audit period, but excluding the first 90 days after diagnosis. There are no flags as seen in Health Checks, only the values listed. The counts are totals during the audit period.

**Dataset field mapping:**

| Column | 2021 field | 2026 field | Notes |
|--------|------------|------------|-------|
| Number of admissions | `hospital_admission_date` / `hospital_admission_reason` | same | Both datasets |
| Number of DKA admissions | `hospital_admission_reason` (DKA value) | same | Both datasets |
| Initial pH at admission | *(absent)* | `blood_gas_ph` | 2026 only; display value from DKA visit |
| Initial bicarbonate at admission | *(absent)* | `blood_gas_bicarbonate` | 2026 only; display value from DKA visit |

### Treatment

This reflects what treatment the patient is currently on. Note that measures here are not scored with flags, but reflect the most recent visit in the audit period where each field is not null. This means that if a patient's latest visit has no entry for a field, the system looks back to the most recent earlier visit where that field was recorded.

**Dataset field mapping:**

| Column | 2021 field | 2026 field | Notes |
|--------|------------|------------|-------|
| Treatment regimen | `treatment` (`TREATMENT_TYPES`) | `insulin_regimen` (`INSULIN_TREATMENT`) | Different constants |
| Glucose monitoring | `glucose_monitoring` (`GLUCOSE_MONITORING_TYPES`) | `cgm_use` (`YES_NO_UNKNOWN`) | 2026 is a simpler yes/no/unknown |
| HCL (hybrid closed loop) | `closed_loop_system in [2,3,4]` → "Yes" | `insulin_regimen == 5` → "Yes" | In 2026 HCL is encoded in the insulin regimen |
| Non-insulin medication | *(absent)* | `non_insulin_medication` (`NON_INSULIN_TREATMENT`) | 2026 only — new column |
| Dietary/lifestyle modification | *(absent)* | `dietary_lifestyle_modification` (`YES_NO_UNKNOWN`) | 2026 only — new column |

### Outcomes

- NHS Number
- Latest HbA1c mmol/mol (%)
- Previous HbA1c mmol/mol (%)
- % change in HbA1c
- Median HbA1c mmol/mol (%)
- Mean HbA1c mmol/mol (%)

This shows the mean and median HbA1c (both as IFCC and DCCT) of all visit HbA1cs in the audit period. The % change reflects the % change in the absolute value of the most recent from the penultimate HbA1c measured as either a positive or negative value, rounded to an integer. Negative is rendered green, positive is rendered amber.

**Dataset field mapping:**

| Column | 2021 field | 2026 field | Notes |
|--------|------------|------------|-------|
| All HbA1c values | `hba1c` + `hba1c_format` + `hba1c_date` | `hba1c` + `hba1c_date` | In 2026 `hba1c_format` is deprecated; values are always mmol/mol. Queries must not rely on `hba1c_format` being non-null for 2026 data. |


## Implementation

### Aim

To Create a new patient report that does not use the KPI class for its calculations, addressing each of the issues above.

This should involve:

- [ ] Please review the KPI class to understand the current measures, the `patient_report.py` to understand the current implementation.
- [ ] Leave the existing implementation in place but that it can be replaced by the new version using a toggle visible only to NPDA audit team members and superusers
- [ ] General principles are to use DaisyUI with the config as used across the application, and use DaisyUI components by default, rather than creating custom ones.
- [ ] Use HTMX for reactive interaction
- [ ] maintain high security posture with existing decorators protecting views, scoping to PDU and role
- [ ] The structure should be broadly similar to the current implementation: button style single choice radiobuttons to toggle between categories; each category shows a different table with the rows for individual patients and columns as listed above.
- [ ] Queries should use the ORM, avoid complexity where possible.
- [ ] The new implementation should include facets in column headers using the `django-filter` dependency
- [ ] Filters should include visits of children with T1 diabetes in an active submission that fall within the audit period. Note that a submission is related to the PDU (through the Submission model) and the patient through the PatientSubmission model.
- [ ] Patients that that have been under the care of a PDU for less than a year (see definition of incomplete year of care above) will score as 'incomplete year of care' for most measures.
- [ ] By default, the table should be sorted with incomplete measures first, then complete, then not required and finally incomplete year of care. Those with an incomplete year of care have background coloured pale orange.
- [ ] It is fine to reuse partials to limit the impact of the refactor

### Detailed Implementation Plan (Agreed)

#### Cohort Definition (Base Query)

- Base cohort: patients with Type 1 diabetes in the active submission for the selected audit period and PDU.
- Scope to visits within the selected audit period.
- Patient identifier: `nhs_number` unless PZ248, then `unique_reference_number`.
- Incomplete year of care, either:
  - Diagnosed in the current audit year (`audit_start_date` <= `Transfer.date_leaving_service` <= `audit_end_date`)
  - Moved out of service in the current audit year (`audit_start_date` <= `Transfer.date_leaving_service` <= `audit_end_date`)

#### Common ORM Building Blocks

- Use `Exists` subqueries for care process completion flags.
- Use `Subquery` for latest and previous visit values where needed.
- Keep querysets filtered to audit period range.
- Sorting default: incomplete first, complete, not required, then incomplete year of care (with background tint).

#### Category-by-Category Query Outline

##### Health Checks

- HbA1c: `Exists` visit with `hba1c` and `hba1c_date` in audit range.
- BMI: `Exists` visit with `bmi` and `height_weight_observation_date` in audit range.
- Thyroid screen: `Exists` visit with `thyroid_function_date` in audit range;
- Blood pressure: `Exists` visit with `systolic_blood_pressure` and `blood_pressure_observation_date` in audit range; only required if >= 12.
- Urinary albumin: `Exists` visit with `albumin_creatinine_ratio` and `albumin_creatinine_ratio_date` in audit range; only required if >= 12.
- Foot exam: `Exists` visit with `foot_examination_observation_date` in audit range; only required if >= 12.
- Eye screen: `Exists` visit with `retinal_screening_observation_date` and `retinal_screening_result` in audit range; not required if < 12. 
  - If not present, return a blank entry in the report not "incomplete". This is because the screen is only mandatory bi-annually.
- Total: `num_passed` vs `num_total` (3 for < 12, 6 for >= 12).

##### Additional Care Processes

- HbA1c 4+: count visits with `hba1c` and `hba1c_date` in audit range >= 4.
- Psychological assessment: `Exists` visit with `psychological_screening_assessment_date` in audit range.
- Smoking status screened: `Exists` visit with `smoking_status` in [non-smoker, smoker] in audit range; not required if < 12.
- Smoking cessation referral: if smoker, `Exists` visit with `smoking_cessation_referral_date` in audit range; not required if non-smoker or < 12.
- Additional dietetic appointment offered: `Exists` visit with `dietician_additional_appointment_offered == Yes` in audit range.
- Patients attending additional dietetic appointment: `Exists` visit with `dietician_additional_appointment_date` in audit range.
- Influenza immunisation recommended: `Exists` visit with `flu_immunisation_recommended_date` in audit range.
- Sick day rules advice: `Exists` visit with `sick_day_rules_training_date` in audit range.
- TODO: 2026 smoke/vape wording and psychological additional support column pending data model and requirements.

##### Care at Diagnosis

- Scope to T1DM patients diagnosed in the audit period (or within agreed 90-day windows where relevant).
- Carbohydrate counting: `Exists` visit with `carbohydrate_counting_level_three_education_date` within -7 to +14 days of diagnosis.
- Coeliac screen: `Exists` visit with `coeliac_screen_date` within +/- 90 days of diagnosis.
- Thyroid screen: `Exists` visit with `thyroid_function_date` within +/- 90 days of diagnosis.
- Not required if diabetes duration > 1 year; incomplete year of care applies if transfer rule is met.
- Add a countdown column for due dates and label late cases as missed (date present but outside window).

##### Admissions

- Filter to patients with at least one admission in the audit period, excluding the first 90 days after diagnosis.
- Number of admissions: `Count` visits with admission start or discharge date in audit range and valid admission reason.
- Number of DKA admissions: `Count` visits with admission reason = DKA in audit range.
- Mean/median HbA1c: compute from valid visits excluding the first 90 days post-diagnosis.
- TODO: initial pH and bicarbonate are pending data model; leave code comments for later.

##### Treatment

- Use the latest `EXISTS` visit in the audit period to derive:
  - Treatment regimen
  - Glucose monitoring
  - HCL (hybrid closed loop)
- Column headings vary by audit period; apply conditional labeling by audit period year.

##### Outcomes

- Base cohort is all patients, not just those with Type 1 diabetes. Still only include patients in the current audit period.
- Latest and previous HbA1c in audit period via `Subquery` ordered by `visit_date`.
- Compute % change between previous and latest HbA1c (rounded).
- Mean and median HbA1c per patient from audit-period values, excluding first 90 days post-diagnosis.

#### Exports and UI Parity

- Ensure CSV/XLSX export matches UI status logic for each category.
- Extend the status icon component to support missed and not-required states.
- Add TODO comments for 2026 fields pending data model updates.
- Add django-filter facets in column headers (completed/eligible counts) for each category, wired to the new ORM querysets.

#### Requirements Coverage Checklist

- UI framework: use DaisyUI components and existing config; avoid custom components where DaisyUI fits.
- Interactivity: HTMX for category switching, sorting, and pagination (reuse existing partials).
- Security: keep current decorators/mixins for OTP login, PDU scoping, and role-based access.
- Structure: category toggle buttons with one table per category, matching current layout.
- Filtering: only T1DM patients in active submissions for the selected audit period and PDU; visits scoped to audit period.
- Facets: per-column completed/eligible counts via django-filter facets.
- Incomplete year of care: based on transfer date within the audit period; apply special styling.
- Default ordering: incomplete first, complete, not required, then incomplete year of care.
- Downloads: keep Excel export; PDF export remains a TODO (issue #1238).
- Reuse: keep existing partials where possible to reduce refactor risk.

#### Verification Plan

- Compare a sample of patients against current KPI-based report for accuracy.
- Validate retinal screening logic for current and previous audit period inclusion.
- Confirm incomplete year of care behavior using transfer records.
- Validate export contents match table contents.