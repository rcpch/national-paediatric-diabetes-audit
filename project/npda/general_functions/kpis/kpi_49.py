from typing import List
from django.db.models import Q


def kpi_49_albuminuria_present(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 49: Albuminuria present

    Numerator: Total number of eligible patients whose most recent entry for for Albuminuria Stage (item 31) based on observation date (item 30) is 2 = Microalbuminuria or 3 = Macroalbuminuria
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
