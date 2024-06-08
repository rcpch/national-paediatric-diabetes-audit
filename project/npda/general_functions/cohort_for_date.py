from datetime import date


def retrieve_cohort_for_date(date_instance: date) -> int:
    """
    Returns the cohort for a given date.
    """
    audit_start_date = date(date.today().year, 4, 1)
    if date_instance < audit_start_date:
        # The patient was audited in the previous year
        days_remaining = (audit_start_date - date_instance).days
    else:
        # The patient was audited in the current year
        audit_end_date = date(date.today().year + 1, 3, 31)
        days_remaining = (audit_start_date - date_instance).days
    total_days = (audit_end_date - audit_start_date).days
    completed_days = total_days - days_remaining
    if (days_remaining / completed_days) < 0.25:
        return 1
    elif (days_remaining / completed_days) < 0.5:
        return 2
    elif (days_remaining / completed_days) < 0.75:
        return 3
    else:
        return 4
