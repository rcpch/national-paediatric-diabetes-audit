from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_38_patients_attending_additional_dietetic_appointment(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 38: Patients attending additional dietetic appointment (%)

    Numerator: Number of eligible patients with at least one entry for Additional Dietitian Appointment Date (item 44) within the audit year
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(
            dietician_additional_appointment_date__range=(
                audit_start_date,
                audit_end_date,
            )
        )
    ).distinct()

    return eligible_visits.count()
