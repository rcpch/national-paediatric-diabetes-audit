from typing import List
from django.db.models import Q


def kpi_30_retinal_screening(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 30: Retinal Screening (%)

    Numerator: Number of eligible patients with at least one entry for Retinal Screening Result (item 28) is either 1 = Normal or 2 = Abnormal AND the observation date (item 27) is within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
