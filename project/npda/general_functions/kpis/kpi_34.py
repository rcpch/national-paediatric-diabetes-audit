from typing import List
from django.db.models import Q


def kpi_34_psychological_assessment(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 34: Psychological assessment (%)

    Numerator: Number of eligible patients with an entry for Psychological Screening Date (item 38) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
