from typing import List
from django.db.models import Q


def kpi_29_urinary_albumin(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 29: Urinary Albumin (%)

    Numerator: Number of eligible patients with at entry for Urinary Albumin Level (item 29) with an observation date (item 30) within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
