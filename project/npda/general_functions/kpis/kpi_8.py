from typing import List
from django.db.models import Q


def kpi_8_total_deaths(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 8: Total number of deaths
    Total number of patients with:
    * a valid NHS number
    * a death date within the audit period
    """
    eligible_patients = patients.filter(
        Q(death_date__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_patients.count()
