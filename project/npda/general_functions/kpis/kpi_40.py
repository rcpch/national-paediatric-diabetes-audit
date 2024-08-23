from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_40_sick_day_rules_advice(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 40: Sick day rules advice (%)

    Numerator: Number of eligible patients with at least one entry for Sick Day Rules (item 47) within the audit period
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = Visit.objects.filter(
        Q(patient__in=patients),
        Q(sick_day_rules_training_date__range=(audit_start_date, audit_end_date)),
    ).distinct()

    return eligible_visits.count()
