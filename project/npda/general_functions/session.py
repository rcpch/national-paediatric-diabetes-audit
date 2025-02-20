from asgiref.sync import sync_to_async
import logging

from django.core.exceptions import PermissionDenied
from django.apps import apps

# NPDA Imports
from project.npda.general_functions import organisations_adapter

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


def create_session_object(user):
    """
    Create a session object for the user, based on their permissions.
    This is called on login, and is used to filter the data the user can see.
    """

    OrganisationEmployer = apps.get_model("npda", "OrganisationEmployer")
    AuditPeriod = apps.get_model("npda", "AuditPeriod")

    primary_organisation = OrganisationEmployer.objects.filter(
        npda_user=user, is_primary_employer=True
    ).get()
    pz_code = primary_organisation.paediatric_diabetes_unit.pz_code
    pdu_choices = (
        organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
            requesting_user=user, user_instance=None
        )
    )

    audit_period = AuditPeriod.objects.get_default_audit_period()
    submission_actions = get_submission_actions(pz_code, audit_period)

    session = {
        "pz_code": pz_code,
        "lead_organisation": primary_organisation.paediatric_diabetes_unit.lead_organisation_name,
        "pdu_choices": list(pdu_choices),
        "selected_audit_period_id": audit_period.pk
    } | submission_actions

    return session


def refresh_session_filters(request, pz_code=None, audit_period_id=None):
    session = {}

    Submission = apps.get_model("npda", "Submission")
    PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
    AuditPeriod = apps.get_model("npda", "AuditPeriod")

    can_upload_csv = True
    can_complete_questionnaire = True

    pz_code = pz_code or request.session.get("pz_code")

    selected_audit_period_id = audit_period_id or request.session.get("selected_audit_period_id")

    if selected_audit_period_id:
        audit_period = AuditPeriod.objects.get(pk=selected_audit_period_id)
    else:
        audit_period = AuditPeriod.objects.get_default_audit_period()

    session["selected_audit_period_id"] = audit_period.pk

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
        session["lead_organisation"] = PaediatricDiabetesUnit.objects.get(
            pz_code=pz_code
        ).lead_organisation_name
        session["pdu_choices"] = list(
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=user, user_instance=None
            )
        )

    session |= get_submission_actions(pz_code, audit_period)

    request.session.update(session)
    request.session.modified = True
