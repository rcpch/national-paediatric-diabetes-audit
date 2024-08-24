from typing import List
from datetime import timedelta
from django.apps import apps
from django.db.models import Q, Avg, F


def kpi_44_mean_hba1c(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 44: Mean HbA1c

    Numerator: Mean of HbA1c measurements (item 17) within the audit period, excluding measurements taken within 90 days of diagnosis
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    eligible_visits = (
        Visit.objects.filter(
            Q(patient__in=patients)
            & Q(visit_date__range=(audit_start_date, audit_end_date))
            & Q(F())
        )
        .exclude(
            Q(hba1c__date__range=(F("patient__diagnosis_date") + timedelta(days=90),))
        )
        .distinct()
    )
    mean_hba1c = eligible_visits.aggregate(mean_hba1c=Avg("hba1c__value"))["mean_hba1c"]

    return mean_hba1c
