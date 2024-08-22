from typing import List
from django.db.models import Q


def kpi_35_smoking_status_screened(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 35: Smoking status screened (%)

    Numerator: Numer of eligible patients with at least one entry for Smoking Status (item 40) that is either 1 = Non-smoker or 2 = Curent smoker within the audit period (based on visit date)
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
