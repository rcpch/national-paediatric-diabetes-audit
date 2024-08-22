from typing import List
from django.db.models import Q


def kpi_22_real_time_cgm_with_alarms(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 22: Number of patients using a real time continuous glucose monitor (CGM) with alarms

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for blood glucose monitoring (item 22) is either 4 = Real time continuous glucose monitor with alarms
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
