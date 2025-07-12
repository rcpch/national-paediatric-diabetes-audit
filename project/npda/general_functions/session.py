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


def get_submission_actions(pz_code, audit_period):
    Submission = apps.get_model("npda", "Submission")

    submission = Submission.objects.filter(
        paediatric_diabetes_unit__pz_code=pz_code,
        submission_active=True,
        audit_period=audit_period,
    ).first()

    can_complete_questionnaire = True
    can_upload_csv = True

    if submission:
        if submission.csv_file:
            can_upload_csv = True
            can_complete_questionnaire = False
        else:
            can_upload_csv = False
            can_complete_questionnaire = True

    return {
        "can_upload_csv": can_upload_csv,
        "can_complete_questionnaire": can_complete_questionnaire,
    }


def get_audit_period_session_data(audit_period, user):
    AuditPeriod = apps.get_model("npda", "AuditPeriod")
    audit_years = []

    for audit_period in AuditPeriod.objects.order_by("start_date").all():
        if audit_period.is_visible or user.is_rcpch_audit_team_member or user.is_superuser:
            audit_years.append(
                {
                    "year": audit_period.audit_year()
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
    OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")
    
    primary_organisation = OrganisationEmployer.objects.filter(
        npda_user=user, is_primary_employer=True
    ).first() # There should only be one primary organisation but if there are multiple, just take the first one
    pz_code = primary_organisation.paediatric_diabetes_unit.pz_code
    pdu_choices = (
        organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
            requesting_user=user, user_instance=None
        )
    )

    # This is the year that that audit period starts in
    audit_period = AuditPeriod.objects.get_default_audit_period()

    submission_actions = get_submission_actions(pz_code, audit_period)
    audit_period_data = get_audit_period_session_data(audit_period, user)

    session = {
        "pz_code": pz_code,
        "parent": primary_organisation.paediatric_diabetes_unit.parent_name,
        "pdu_choices": list(pdu_choices),
        "selected_audit_year": audit_period.audit_year(),
    } | submission_actions | audit_period_data

    return session


def refresh_session_filters(request, pz_code=None, audit_year=None, csv_upload=None, questionnaire=None):
    session = {}

    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
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
        session["parent"] = PaediatricDiabetesUnit.objects.get(
            pz_code=pz_code,
            active=True
        ).parent_name
        session["pdu_choices"] = list(
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=user, user_instance=None
            )
        )

    if csv_upload:
        session |= {
            "can_upload_csv": True,
            "can_complete_questionnaire": False,
        }
    elif questionnaire:
        session |= {
            "can_upload_csv": False,
            "can_complete_questionnaire": True,
        }
    else:
        session |= get_submission_actions(pz_code, audit_period)
    
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