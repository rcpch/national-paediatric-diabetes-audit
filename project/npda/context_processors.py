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


def context_from_settings(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "instance_label": settings.INSTANCE_LABEL
    }
