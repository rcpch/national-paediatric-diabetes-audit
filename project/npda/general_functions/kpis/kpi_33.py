from typing import List
from django.db.models import Q


def kpi_33_hba1c_4plus(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 33: HbA1c 4+ (%)

    Numerator: Number of eligible patients with at least four entries for HbA1c value (item 17) with an observation date (item 19) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
