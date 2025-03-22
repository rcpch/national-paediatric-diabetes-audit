from datetime import datetime
from django.conf import settings
from project.npda.general_functions import get_current_audit_year


def session_data(request):
    return {
        "can_complete_questionnaire": request.session.get(
            "can_complete_questionnaire", False
        ),
        "can_upload_csv": request.session.get("can_upload_csv", False),
        "pz_code": request.session.get("pz_code", None),
        "lead_organisation": request.session.get("lead_organisation", None),
        "requested_audit_year": request.session.get("requested_audit_year", None),
        "audit_years": request.session.get("audit_years", []),
        "lead_organisation": request.session.get("lead_organisation", None),
    }


def can_do_ui_actions(request):
    session_is_audit_year_open = request.session.get("selected_audit_year") == get_current_audit_year()
    session_can_use_questionnaire = request.session.get("can_complete_questionnaire", True)

    is_admin = request.user.is_superuser or request.user.is_rcpch_audit_team_member

    return {
        "is_audit_year_open": session_is_audit_year_open,
        "can_alter_this_audit_year_submission": session_is_audit_year_open or is_admin,
        "can_use_questionnaire": session_can_use_questionnaire or is_admin,
    }


def context_from_settings(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "instance_label": settings.INSTANCE_LABEL
    }
