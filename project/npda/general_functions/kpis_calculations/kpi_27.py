from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_27_thyroid_screen(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 27: Thyroid Screen (%)

    Numerator: Number of eligible patients with at least one entry for Thyroid function observation date (item 34) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(thyroid_function_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
