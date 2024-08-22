from typing import List
from django.db.models import Q


def kpi_32_health_check_completion_rate(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 32: Health check completion rate (%)

    Numerator: Number of eligible patients with care processes 25,26,27,28,29, and 31 completed in the audit period
    Denominator:
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
