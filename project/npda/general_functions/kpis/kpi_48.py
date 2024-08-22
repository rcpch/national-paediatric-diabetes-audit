from typing import List
from django.db.models import Q


def kpi_48_required_additional_psychological_support(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 48: Required additional psychological support

    Numerator: Total number of eligible patients with at least one entry for Psychological Support (item 39) that is 1 = Yes within the audit period (based on visit date)
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
