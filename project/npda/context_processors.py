from datetime import datetime
from django.conf import settings
from project.npda.models.audit_period import AuditPeriod


def session_data(request):
    # Permission checking done in @check_data_permissions, CheckPDUListMixin or CheckPDUInstanceMixin
    # We are fine to trust it here as this is for rendering purposes
    pz_code = request.resolver_match.kwargs.get("pz_code", request.session.get("pz_code", None))

    audit_period_slug = request.resolver_match.kwargs.get("audit_period", None)

    # Temporary hack until all pages migrated over to new URL structure
    if not audit_period_slug:
        audit_year = request.session.get("selected_audit_year", None)

        if audit_year:
            audit_period_slug = f"{audit_year}-{audit_year+1}"

    return {
        "can_complete_questionnaire": request.session.get(
            "can_complete_questionnaire", False
        ),
        "can_upload_csv": request.session.get("can_upload_csv", False),
        # Required for the url-data helper
        "pz_code": pz_code,
        "audit_period_slug": audit_period_slug,
        "parent_name": request.session.get("parent_name", None),
        "audit_years": request.session.get("audit_years", []),
    }


def context_from_settings(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "instance_label": settings.INSTANCE_LABEL
    }
