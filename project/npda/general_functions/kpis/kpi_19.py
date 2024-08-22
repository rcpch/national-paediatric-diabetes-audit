from typing import List
from django.db.models import Q


def kpi_19_dietary_management_alone(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 19: Dietary management alone (no insulin or other diabetes related medication)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 7 = Dietary management alone (no insulin or other diabetes related medication)
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
