from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_10_total_coeliacs(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 10: Total number of coeliacs
    Number of eligible patients (measure 1) whose most recent observation for item 37 (based on visit date) is 1 = Yes
    """
    eligible_patients = patients.objects.filter(
        # TODO # This calculation is part of issue #88 discussion
    ).distinct()

    return eligible_patients.count()
