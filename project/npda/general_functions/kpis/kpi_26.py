from typing import List
from django.db.models import Q


def kpi_26_bmi(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 26: BMI (%)

    Numerator: Number of eligible patients at least one valid entry for Patient Height (item 14) and for Patient Weight (item 15) with an observation date (item 16) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
