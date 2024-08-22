from typing import List
from django.db.models import Q


def kpi_13_one_to_three_injections_per_day(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 13: One - three injections/day
    Nominator: Total number of eligible patients (measure 1)
    Denominator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 1 = One-three injections/day
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
