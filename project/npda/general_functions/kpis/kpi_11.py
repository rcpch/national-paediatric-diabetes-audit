from typing import List
from django.db.models import Q


def kpi_11_total_thyroids(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 11: Number of patients with thyroid  disease
    Number of eligible patients (measure 1)
    whose most recent observation for item 35 (based on visit date)
    is either 2 = Thyroxine for hypothyroidism or 3 = Antithyroid medication for hyperthyroidism
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
