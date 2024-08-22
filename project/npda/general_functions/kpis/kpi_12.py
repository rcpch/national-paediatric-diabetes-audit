from typing import List
from django.db.models import Q


def kpi_12_total_ketone_test_equipment(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 12: Number of patients using (or trained to use) blood ketone testing equipment
    Number of eligible patients (measure 1) whose most recent observation for item 45 (based on visit date) is 1 = Yes
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
