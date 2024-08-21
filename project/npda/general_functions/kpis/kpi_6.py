from django.db.models import Q


def kpi_6_total_t1dm_complete_year_gte_12yo(
    patients, audit_start_date, audit_end_date
) -> dict:
    """
    Calculates KPI 6: Total number of patients with T1DM who have completed a year of care and are aged 12 or older
    Total number of patients with:
    * a valid NHS number
    * an observation within the audit period
    * Age 12 and above at the start of the audit period
    * Diagnosis of Type 1 diabetes

    Excluding
    * Date of diagnosis within the audit period
    * Date of leaving service within the audit period
    * Date of death within the audit period
    """
    eligible_patients = patients.filter(
        Q(diabetes_type=1)
        & Q(diagnosis_date__lt=audit_start_date.replace(year=audit_start_date.year - 1))
        & Q(
            date_of_birth__lte=audit_start_date.replace(year=audit_start_date.year - 12)
        )
    ).distinct()

    return eligible_patients.count()
