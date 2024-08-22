from django.db.models import Q


def kpi_2_total_new_diagnoses(patients, audit_start_date, audit_end_date) -> dict:
    """
    Calculates KPI 2: Total number of new diagnoses within the audit period
    "Total number of patients with:
    * a valid NHS number
    *a valid date of birth
    *a valid PDU number
    * a visit date or admission date within the audit period
    * Below the age of 25 at the start of the audit period
    * Date of diagnosis within the audit period"
    """
    eligible_patients = patients.filter(
        # Valid attributes
        Q(nhs_number__isnull=False)
        & Q(date_of_birth__isnull=False)
        # NOTE: should be already filtered out when setting
        # patients in init method, but adding for clarity
        & Q(site__paediatric_diabetes_unit__pz_code__isnull=False)
        # Visit / admisison date within audit period
        & Q(visit__visit_date__range=(audit_start_date, audit_end_date))
        # Below the age of 25 at the start of the audit period
        & Q(date_of_birth__gt=audit_start_date.replace(year=audit_start_date.year - 25))
        # Diagnosis date within audit period
        & Q(diagnosis_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
