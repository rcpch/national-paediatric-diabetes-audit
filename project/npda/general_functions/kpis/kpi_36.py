from typing import List
from django.db.models import Q


def kpi_36_referral_to_smoking_cessation_service(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 36: Referral to smoking cessation service (%)

    Numerator: Number of eligible patients with an entry for Date of Smoking Cessation Referral (item 41) within the audit period
    Denominator: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in audit period (measure 6)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
