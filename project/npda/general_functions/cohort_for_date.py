from datetime import date


def retrieve_cohort_for_date(date_instance: date) -> int:
    """
    Returns the cohort number of the patient for a given submission date (today)

    A cohort simply is defined as the quarter of the audit year the submission date lies in

    **The audit year starts on the 1st of April and ends on the 31st of March the following year**
    Returns cohort = 4 if the patient has less than 25% of the audit year remaining
    Returns cohort = 3 if the patient has less than 50% of the audit year remaining
    Returns cohort = 2 if the patient has less than 75% of the audit year remaining
    Returns cohort = 1 if the patient has more than 75% of the audit year remaining
    """
    # Audit start date is on the 1st April every year
    audit_start_date = date(date_instance.year, 4, 1)
    if date_instance < audit_start_date:
        # The patient was audited in the previous year
        audit_start_date = date(date_instance.year - 1, 4, 1)
        audit_end_date = date(date_instance.year, 3, 31)
        days_elapsed = (date_instance - audit_start_date).days
    else:
        # The patient was audited in the current year
        # Audit end date is on the 31st of March of every year
        audit_end_date = date(date_instance.year + 1, 3, 31)
        days_elapsed = (date_instance - audit_start_date).days
    total_days = (audit_end_date - audit_start_date).days
    if (days_elapsed / total_days) < 0.25:
        return 1
    elif (days_elapsed / total_days) < 0.5:
        return 2
    elif (days_elapsed / total_days) < 0.75:
        return 3
    else:
        return 4
