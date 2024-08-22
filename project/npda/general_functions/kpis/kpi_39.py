from typing import List
from django.db.models import Q


def kpi_39_influenza_immunisation_recommended(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 39: Influenza immunisation recommended (%)

    Numerator: Number of eligible patients with at least one entry for Influzena Immunisation Recommended (item 24) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
