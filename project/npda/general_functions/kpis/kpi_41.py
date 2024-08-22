from typing import List
from django.db.models import Q


def kpi_41_coeliac_disease_screening(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 41: Coeliac diasease screening (%)

    Numerator: Number of eligible patients with an entry for Coeliac Disease Screening Date (item 36) within 90 days of Date of Diabetes Diagnosis (item 7)
    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
