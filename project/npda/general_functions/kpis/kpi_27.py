from typing import List
from django.db.models import Q


def kpi_27_thyroid_screen(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 27: Thyroid Screen (%)

    Numerator: Number of eligible patients with at least one entry for Thyroid function observation date (item 34) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
