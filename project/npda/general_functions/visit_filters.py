# python imports
from datetime import date

# Django imports
from django.db.models import Q
from django.utils import timezone

# RCPCH imports
from ...constants import ALL_VISIT_DATES


def visit_falls_within_audit_period_Q_object(
    audit_start_date: date, prepend_query_path: str = None
) -> Q:
    """
    This function returns a Q object that can be used to filter for ANY visits that have a date across all the measures that falls within the selected audit year.
    It accepts an optional prepend query path if the returned Q object needs to traverse a relationship to the visit
    instance.

    Note that postgres prefers timezone aware dates, so the audit_start_date is converted to a timezone aware date.
    """
    audit_start_date = timezone.datetime(year=audit_start_date.year, month=4, day=1)
    audit_end_date = timezone.datetime(year=audit_start_date.year + 1, month=3, day=31)

    filter_dict = Q()  # Q object to return
    if prepend_query_path:
        prepend_query_path = f"{prepend_query_path}__"
    else:
        prepend_query_path = ""

    for visit_date in ALL_VISIT_DATES:
        # loops through all the potential dates in a visit instance and returns a Q object that can be used to filter
        # visits that fall within the audit period
        visit_Q = Q(
            **{
                f"{prepend_query_path}{visit_date[0]}__gte": audit_start_date,
                f"{prepend_query_path}{visit_date[0]}__lte": audit_end_date,
            }
        )
        filter_dict |= visit_Q

    return filter_dict
