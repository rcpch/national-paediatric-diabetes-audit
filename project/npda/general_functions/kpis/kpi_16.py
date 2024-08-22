from typing import List
from django.db.models import Q


def kpi_16_one_to_three_injections_plus_other_medication(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 16: Insulin pump (including those using a pump as part of a hybrid closed loop)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 3 = Insulin pump
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
