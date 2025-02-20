from datetime import datetime

from project.npda.general_functions import get_current_audit_year
from project.npda.models import AuditPeriod


def get_selected_audit_period(request):
    # TODO MRB: cache all this
    selected_audit_period_id = request.session.get("selected_audit_period_id", None)

    if selected_audit_period_id:
        return AuditPeriod.objects.get(pk=selected_audit_period_id)


def session_data(request):
    return {
        "can_complete_questionnaire": request.session.get(
            "can_complete_questionnaire", False
        ),
        "can_upload_csv": request.session.get("can_upload_csv", False),
        "pz_code": request.session.get("pz_code", None),
        "lead_organisation": request.session.get("lead_organisation", None),
        "selected_audit_period": get_selected_audit_period(request),
        "audit_periods": AuditPeriod.objects.all()
    }


def can_alter_this_audit_year_submission(request):
    can_alter_this_audit_year_submission = False

    if(audit_period := get_selected_audit_period(request)):
        can_alter_this_audit_year_submission = audit_period.is_allowed_to_edit(request.user)

    return {
        "can_alter_this_audit_year_submission": can_alter_this_audit_year_submission
    }


def can_use_questionnaire(request):
    """
    This context processor is used to determine if the user can use the questionnaire.
    If the user is an admin, they can always use the questionnaire.
    If the user is not an admin, they can only use the questionnaire if they have not uploaded a csv.
    """
    if hasattr(request.user, "is_rcpch_audit_team_member"):
        if request.user.is_rcpch_audit_team_member:
            return {"can_use_questionnaire": True}

    if request.user.is_superuser or request.session.get(
        "can_complete_questionnaire", True
    ):
        return {"can_use_questionnaire": True}

    return {"can_use_questionnaire": False}
