from asgiref.sync import sync_to_async
import logging

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.utils import timezone

# NPDA Imports
from project.npda.general_functions import (
    organisations_adapter,
    get_client_ip,
)

logger = logging.getLogger(__name__)


def get_audit_period_session_data(audit_period, user):
    AuditPeriod = apps.get_model("npda", "AuditPeriod")
    audit_years = []

    for audit_period in AuditPeriod.objects.order_by("start_date").all():
        if audit_period.is_visible or user.is_rcpch_audit_team_member or user.is_superuser:
            audit_years.append(
                {
                    "year": audit_period.audit_year(),
                    "slug": audit_period.slug
                }
            )
    
    return {
        "audit_years": audit_years
    }


def create_session_object(user):
    """
    Create a session object for the user, based on their permissions.
    This is called on login, and is used to filter the data the user can see.
    """
    AuditPeriod = apps.get_model("npda", "AuditPeriod")
    
    pz_code = user.primary_pdu().pz_code
    pdu_choices = (
        organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
            requesting_user=user, user_instance=None
        )
    )

    # This is the year that that audit period starts in
    audit_period = AuditPeriod.objects.get_default_audit_period()

    audit_period_data = get_audit_period_session_data(audit_period, user)

    session = {
        "pz_code": pz_code,
        "pdu_choices": list(pdu_choices),
        "selected_audit_year": audit_period.audit_year(),
    } | audit_period_data

    return session


def refresh_session_filters(request, pz_code=None, audit_year=None):
    session = {}

    AuditPeriod = apps.get_model("npda", "AuditPeriod")

    pz_code = pz_code or request.session.get("pz_code")

    audit_year = audit_year or request.session.get("selected_audit_year")

    audit_period = AuditPeriod.objects.get(
        start_date__year=audit_year
    )

    session["selected_audit_year"] = audit_year

    if pz_code:
        user = request.user

        can_see_organisations = (
            user.is_rcpch_audit_team_member
            or user.organisation_employers.filter(pz_code=pz_code).exists()
        )

        if not can_see_organisations:
            logger.warning(
                f"User {user} requested organisation {pz_code} they cannot see"
            )
            raise PermissionDenied()

        session["pz_code"] = pz_code
        session["pdu_choices"] = list(
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=user, user_instance=None
            )
        )
    
    session |= get_audit_period_session_data(audit_period, request.user)

    request.session.update(session)
    request.session.modified = True

def save_csv_uploading_user_to_visitactivity(request):
    """
    Save the user who is uploading a CSV to the VisitActivity model.
    This is used to track who is uploading CSVs and when.
    """
    VisitActivity = apps.get_model("npda", "VisitActivity")
    
    # Create VisitActivity entry for the user
    VisitActivity.objects.create(
        npdauser=request.user,
        activity=8,  # UPLOADED_CSV
        ip_address=get_client_ip(request=request),
        activity_datetime=timezone.now(),
    )