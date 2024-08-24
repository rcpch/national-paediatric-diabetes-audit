from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_18_insulin_pump_plus_other_medication(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 18: Insulin pump therapy plus other blood glucose lowering medication

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 6 = Insulin pump therapy plus other blood glucose lowering medication
    Denominator: Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(treatment=6)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
