from typing import List
from django.db.models import Q


def kpi_9_total_service_transitions(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 9: Total number of service transitions
    Total number of patients with:
    * a valid NHS number
    * a service transition date within the audit period
    """
    eligible_patients = patients.filter(
        Q(site__date_leaving_service__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_patients.count()
