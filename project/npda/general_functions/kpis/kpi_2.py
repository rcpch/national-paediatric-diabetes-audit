from django.db.models import Q


def kpi_2_total_new_diagnoses(patients, audit_start_date, audit_end_date) -> dict:
    """
    Calculates KPI 2:
    Total number of patients with:
            * a diagnosis date within the audit period
    """
    eligible_patients = patients.filter(
        # Diagnosis date within audit period
        Q(diagnosis_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
