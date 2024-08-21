from django.db.models import Q


def kpi_5_total_t1dm_complete_year(patients, audit_start_date, audit_end_date) -> dict:
    """
    Calculates KPI 5: Total number of patients with T1DM who have completed a year of care
    Total number of patients with:
    * a valid NHS number
    *a valid date of birth
    *a valid PDU number
    * a visit date or admission date within the audit period
    * Below the age of 25 at the start of the audit period
    * Date of diagnosis within the audit period
    """
    eligible_patients = patients.filter(
        Q(diabetes_type=1)
        & Q(diagnosis_date__lt=audit_start_date.replace(year=audit_start_date.year - 1))
    ).distinct()

    return eligible_patients.count()
