from typing import List
from django.apps import apps
from django.db.models import Q


def kpi_25_hba1c(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 25: HbA1c (%)

    Numerator: Number of eligible patients with at least one valid entry for HbA1c value (item 17) with an observation date (item 19) within the audit period
    Denominator: Number of patients with Type 1 diabetes with a complete year of care in the audit period (measure 5)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_patients = Visit.objects.filter(
        Q(patient__in=patients)
        & Q(hba1c__isnull=False)
        & Q(hba1c_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
