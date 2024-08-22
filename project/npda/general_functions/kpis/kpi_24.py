from typing import List
from django.db.models import Q


def kpi_24_hybrid_closed_loop_system(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 24: Hybrid closed loop system (HCL)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is either 3 = insulin pump or 6 = Insulin pump therapy plus other blood glucose lowering medication AND whose most recent entry for item 21 (based on visit date) is either 2 = Closed loop system (licenced) or 3 = Closed loop system (DIY, unlicenced) or 4 = Closed loop system (licence status unknown)
    Denominator: Total number of eligible patients (measure 1)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
