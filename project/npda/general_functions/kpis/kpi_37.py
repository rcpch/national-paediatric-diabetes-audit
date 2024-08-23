from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_37_additional_dietetic_appointment_offered(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 37: Additional dietetic appointment offered (%)

    Numerator: Numer of eligible patients with at least one entry for Additional Dietitian Appointment Offered (item 43) that is 1 = Yes within the audit period (based on visit date)
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
        & Q(dietician_additional_appointment_offered=1)
    ).distinct()

    return eligible_patients.count()
