from typing import List
from django.db.models import Q


def kpi_38_patients_attending_additional_dietetic_appointment(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 38: Patients attending additional dietetic appointment (%)

    Numerator: Number of eligible patients with at least one entry for Additional Dietitian Appointment Date (item 44) within the audit year
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
