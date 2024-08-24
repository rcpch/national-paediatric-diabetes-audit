from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_21_flash_glucose_monitor(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 21: Number of patients using a flash glucose monitor

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 8 = Dietary management plus other blood glucose lowering medication (non Type-1 diabetes)
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(treatment=8)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
