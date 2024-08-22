from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_17_four_or_more_injections_plus_other_medication(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 17: One - three injections/day plus other blood glucose lowering medication

    Numerator: Number of eligible patients whose most recent entry (based on visit date) for treatment regimen (item 20) is 4 = One - three injections/day plus other blood glucose lowering medication
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(treatment=3)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
