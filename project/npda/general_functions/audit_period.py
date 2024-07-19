from datetime import date


def get_audit_period_for_date(input_date: date) -> tuple[date, date]:
    """Get the start and end date of the audit period for the given date.

    :param date: The date
    :return: (audit_start_date, audit_end_date)

    Data:
        Audit Period	Audit period start	Audit period end
        2024 - 2025	        1-Apr-24	        31-Mar-25
        2025 - 2026	        1-Apr-25	        31-Mar-26
        2026 - 2027	        1-Apr-26	        31-Mar-27

    NOTE: dates outside of the audit period will raise
          a ValueError as undefined.
    """

    if input_date < date(2024, 4, 1) or input_date > date(2027, 3, 31):
        raise ValueError("Audit period is only available for the years 2024 to 2027")

    # Audit year is the year of the input date if the month is April or later, otherwise it is the previous year
    audit_year = input_date.year if input_date.month >= 4 else input_date.year - 1

    # Start date is always 1st April
    audit_start_date = date(audit_year, 4, 1)

    # End date is always 31st March of the following year
    audit_end_date = date(audit_year + 1, 3, 31)

    return audit_start_date, audit_end_date
