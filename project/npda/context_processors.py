from datetime import datetime
from django.conf import settings
from project.npda.models.audit_period import AuditPeriod


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
    audit_period = AuditPeriod.objects.get_audit_period_for_request(request)

    session_is_audit_year_open = audit_period and audit_period.is_open
    session_can_upload_csv = request.session.get("can_upload_csv", True)
    session_can_use_questionnaire = request.session.get("can_complete_questionnaire", True)

    can_override_data_upload_rules = request.user.is_superuser or getattr(request.user, "is_rcpch_audit_team_member", False)
    data_upload_rules_overridden = can_override_data_upload_rules and request.GET.get("unlock", False)

    return {
        "is_audit_year_open": session_is_audit_year_open,
        "is_csv_upload": session_can_upload_csv,
        "is_questionnaire": session_can_use_questionnaire,
        "can_override_data_upload_rules": can_override_data_upload_rules,
        "data_upload_rules_overridden": data_upload_rules_overridden,
        # For compatibility with existing templates
        "can_alter_this_audit_year_submission": data_upload_rules_overridden or session_is_audit_year_open,
        "can_use_questionnaire": data_upload_rules_overridden or (session_is_audit_year_open and session_can_use_questionnaire),
    }


def context_from_settings(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "instance_label": settings.INSTANCE_LABEL
    }
