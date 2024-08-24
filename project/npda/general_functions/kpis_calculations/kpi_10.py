from typing import List
from django.apps import apps
from django.apps import apps
from django.db.models import Q


def kpi_10_total_coeliacs(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 10: Total number of coeliacs
    Number of eligible patients (measure 1) whose most recent observation for item 37 (based on visit date) is 1 = Yes
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(gluten_free_diet=1)
        & Q(visit_date__range=[audit_start_date, audit_end_date])
    ).distinct()

    return eligible_visits.count()
