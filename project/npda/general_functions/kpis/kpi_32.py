from typing import List
from django.db.models import Q
from django.apps import apps


def kpi_32_health_check_completion_rate(
    patients: List[dict], audit_start_date: str, audit_end_date: str
) -> dict:
    """
    Calculates KPI 32: Health check completion rate (%)

    Numerator: Number of eligible patients with care processes 25,26,27,28,29, and 31 completed in the audit period
    Denominator:
    """
    eligible_patients = patients.filter(
        Q(patient__in=patients)
        & Q(hba1c__isnull=False)
        & Q(hba1c_date__range=(audit_start_date, audit_end_date))
        & Q(weight__isnull=False)
        & Q(height__isnull=False)
        & Q(height_weight_observation_date__range=(audit_start_date, audit_end_date))
        & Q(thyroid_function_date__range=(audit_start_date, audit_end_date))
        & Q(systolic_blood_pressure__isnull=False)
        & Q(height__isnull=False)
        & Q(blood_pressure_observation_date__range=(audit_start_date, audit_end_date))
        & Q(albumin_creatinine_ratio__isnull=False)
        & Q(albumin_creatinine_ratio_date__range=(audit_start_date, audit_end_date))
        & Q(foot_examination_observation_date__range=(audit_start_date, audit_end_date))
    ).distinct()

    return eligible_patients.count()
