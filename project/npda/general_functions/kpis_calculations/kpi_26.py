from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_26_bmi(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 26: BMI (%)

    Numerator: Number of eligible patients at least one valid entry for Patient Height (item 14) and for Patient Weight (item 15) with an observation date (item 16) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(weight__isnull=False)
        & Q(height__isnull=False)
        & Q(height_weight_observation_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
