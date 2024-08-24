from django.db.models import Q


def kpi_6_total_t1dm_complete_year_gte_12yo(
    patients, audit_start_date, audit_end_date
) -> dict:
    """
    Calculates KPI 6: Total number of patients with T1DM who have completed a year of care and are aged 12 or older
    Total number of patients with:
    * a valid NHS number
    * an observation within the audit period
    * Age 12 and above at the start of the audit period
    * Diagnosis of Type 1 diabetes

    Excluding
    * Date of diagnosis within the audit period
    * Date of leaving service within the audit period
    * Date of death within the audit period
    """
    eligible_patients = (
        patients.filter(
            Q(nhs_number__isnull=False)
            # valid NHS number
            # NOTE: should be already filtered out when setting
            # patients in init method, but adding for clarity
            & Q(site__paediatric_diabetes_unit__pz_code__isnull=False)
            # Visit / admisison date within audit period
            & Q(visit__visit_date__range=(audit_start_date, audit_end_date))
            # Over 12 years old at the start of the audit period
            & Q(
                date_of_birth__lte=audit_start_date.replace(
                    year=audit_start_date.year - 12
                )
            )
            # is type 1 diabetes
            & Q(diabetes_type=1)
        )
        .exclude(
            # Diagnosis date within audit period
            Q(diagnosis_date__range=(audit_start_date, audit_end_date))
            # Date of leaving service within the audit period
            | Q(site__date_leaving_service__range=(audit_start_date, audit_end_date))
            # Date of death within the audit period
            | Q(date_of_death__range=(audit_start_date, audit_end_date))
        )
        .distinct()
    )

    return eligible_patients.count()
