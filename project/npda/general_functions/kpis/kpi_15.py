from typing import List
from django.db.models import Q


def kpi_15_insulin_pump(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 15: Insulin pump (including those using a pump as part of a hybrid closed loop)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 3 = Insulin pump
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
