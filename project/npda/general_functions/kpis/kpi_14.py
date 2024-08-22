from typing import List
from django.db.models import Q


def kpi_14_four_or_more_injections_per_day(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 14: Four or more injections/day

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 2 = Four or more injections/day
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
