from django.db.models import Q


def kpi_4_total_t1dm_gte_12yo(patients, audit_start_date) -> dict:
    """
    Calculates KPI 4: Total number of patients with T1DM aged 12 or older
        Total number of patients with:
            * T1DM
            * aged 12 or older
    """
    eligible_patients = patients.filter(
        Q(diabetes_type=1)
        & Q(date_of_birth__lt=audit_start_date.replace(year=audit_start_date.year - 12))
    ).distinct()

    return eligible_patients.count()
