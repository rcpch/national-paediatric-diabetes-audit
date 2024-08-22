from typing import List
from django.db.models import Q


def kpi_8_total_deaths(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 8: Number of patients who died within audit period
    Number of eligible patients (measure 1) with a death date in the audit period
    """
    eligible_patients = patients.filter(
        Q(death_date__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_patients.count()
