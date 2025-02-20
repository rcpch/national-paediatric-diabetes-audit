import logging
from datetime import datetime, date

from django.apps import apps


logger = logging.getLogger(__name__)


def audit_periods_seeder():
    AuditPeriod = apps.get_model("npda", "AuditPeriod")

    today = datetime.now()

    this_year = today.year
    next_year = this_year + 1

    if AuditPeriod.objects.count() > 0:
        logger.info(
            "AuditPeriods already exist in the databases, not creating any new ones..."
        )
    else:
        # 2023 was the last year with the old system
        # we uploaded data from then to test this one 
        for year in range(2023, next_year):
            audit_start_date = date(year, 4, 1)
            audit_end_date = date(year + 1, 3, 31)

            is_open = today.date() >= audit_start_date and today.date() <= audit_end_date

            AuditPeriod.objects.create(
                is_open=is_open, start_date=audit_start_date, end_date=audit_end_date
            )