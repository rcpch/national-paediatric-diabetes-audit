from typing import List
from django.db.models import Q


def kpi_45_median_hba1c(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 45: Median HbA1c

    Numerator: Median of HbA1c measurements (item 17) within the audit period, excluding measurements waken within 90 days of diagnosis
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
