from datetime import date

from django.db.models import Q
from django.db.models import QuerySet

from project.npda.models import Patient


def kpi_1_total_eligible(
    patients: QuerySet[Patient], audit_start_date: date, audit_end_date: date
) -> int:
    """Calculates KPI 1: Total number of eligible patients
    Total number of patients with:
        * a valid NHS number
        *a valid date of birth
        *a valid PDU number
        * a visit date or admission date within the audit period
        * Below the age of 25 at the start of the audit period
    """

    eligible_patients = patients.filter(
        # Valid attributes
        Q(nhs_number__isnull=False)
        & Q(date_of_birth__isnull=False)
        # Visit / admisison date within audit period
        & Q(visit__visit_date__range=(audit_start_date, audit_end_date))
        # Below the age of 25 at the start of the audit period
        & Q(date_of_birth__gt=audit_start_date.replace(year=audit_start_date.year - 25))
    ).distinct()

    return eligible_patients.count()
