from typing import List
from django.db.models import Q


def kpi_46_number_of_admissions(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 46: Number of admissions

    Numerator: Total number of admissions with a valid reason for admission (item 50) AND with a start date (item 48) OR discharge date (item 49)within the audit period
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
