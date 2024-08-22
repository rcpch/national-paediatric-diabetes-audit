from typing import List
from django.db.models import Q


def kpi_28_blood_pressure(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 28: Blood Pressure (%)

    Numerator: Number of eligible patients with a valid entry for systolic measurement (item 23) with an observation date (item 25) within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
