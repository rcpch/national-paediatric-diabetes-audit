from django.db.models import Q


def kpi_3_total_t1dm(patients, audit_start_date, audit_end_date) -> dict:
    """
    Calculates KPI 3: Total number of patients with T1DM
        Total number of patients with:
            * T1DM

    (1, Type 1 Insulin-Dependent Diabetes Mellitus)
    """
    eligible_patients = patients.filter(diabetes_type=1).distinct()

    return eligible_patients.count()
