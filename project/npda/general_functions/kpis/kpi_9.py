from typing import List
from django.db.models import Q


def kpi_9_total_service_transitions(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 9: Number of patients who transitioned/left service within audit period
    Number of eligible patients (measure 1) with a leaving date in the audit period
    """
    eligible_patients = patients.filter(
        Q(site__date_leaving_service__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_patients.count()
