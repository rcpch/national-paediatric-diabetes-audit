from django.db.models import Q


def kpi_3_total_t1dm(patients, audit_start_date, audit_end_date) -> dict:
    """
    Calculates KPI 3: Total number of eligible patients with Type 1 diabetes
    Total number of patients with:
        * a valid NHS number
        *a valid date of birth
        *a valid PDU number
        * a visit date or admission date within the audit period
        * Below the age of 25 at the start of the audit period
        * Diagnosis of Type 1 diabetes"

    (1, Type 1 Insulin-Dependent Diabetes Mellitus)
    """
    eligible_patients = patients.filter(
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
        & Q(diabetes_type=1)
        # is type 1 diabetes
    ).distinct()

    return eligible_patients.count()
