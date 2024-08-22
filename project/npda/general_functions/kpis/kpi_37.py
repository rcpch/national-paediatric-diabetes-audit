from typing import List
from django.db.models import Q


def kpi_37_additional_dietetic_appointment_offered(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 37: Additional dietetic appointment offered (%)

    Numerator: Numer of eligible patients with at least one entry for Additional Dietitian Appointment Offered (item 43) that is 1 = Yes within the audit period (based on visit date)
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    eligible_patients = patients.filter(Q()).distinct()

    return eligible_patients.count()
