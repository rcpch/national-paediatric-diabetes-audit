from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_19_dietary_management_alone(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 19: Dietary management alone (no insulin or other diabetes related medication)

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 7 = Dietary management alone (no insulin or other diabetes related medication)
    Denominator: Total number of eligible patients (measure 1)
    """

    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(treatment=7)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
