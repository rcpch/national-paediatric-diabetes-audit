from typing import List
from django.db.models import Q


def kpi_31_foot_examination(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 31: Foot Examination (%)

    Numerator: Number of eligible patients with at least one entry for Foot Examination Date (item 26) within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
