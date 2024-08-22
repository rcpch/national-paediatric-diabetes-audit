from typing import List
from django.db.models import Q


def kpi_43_carbohydrate_counting_education(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 43: Carbohydrate counting education (%)

    Numerator: Number of eligible patients with an entry for Carbohydrate Counting Education (item 42) within 7 days before or 14 days after the Date of Diabetes Diagnosis (item 7)
    Denominator: Number of patients with Type 1 diabetes who were diagnosed at least 90 days before the end of the audit period
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
