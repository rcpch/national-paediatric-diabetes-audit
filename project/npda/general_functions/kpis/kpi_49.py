from typing import List
from django.apps import apps
from django.db.models import Q, Max


def kpi_49_albuminuria_present(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 49: Albuminuria present

    Numerator: Total number of eligible patients whose most recent entry for for Albuminuria Stage (item 31) based on observation date (item 30) is 2 = Microalbuminuria or 3 = Macroalbuminuria
    Denominator: Total number of eligible patients (measure 1)
    """
    Visit = apps.get_model("npda", "Visit")
    acrs_for_patient = Visit.objects.filter(
        Q(albumin_creatinine_ratio_date__range=(audit_start_date, audit_end_date))
        & (Q(albuminuria_stage=2) | Q(albuminuria_stage=3))
        & Q(patient__in=patients)
    )
    latest_raised_acr_visits = acrs_for_patient.values("patient").annotate(
        max_acr_date=Max("albumin_creatinine_ratio_date")
    )
    matched_visits = acrs_for_patient.filter(
        albumin_creatinine_ratio_date__in=latest_raised_acr_visits.values(
            "max_acr_date"
        )
    )
    return matched_visits.count()
