from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_12_total_ketone_test_equipment(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 12: Number of patients using (or trained to use) blood ketone testing equipment
    Number of eligible patients (measure 1) whose most recent observation for item 45 (based on visit date) is 1 = Yes
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(ketone_meter_training=1)
        & Q(visit_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
