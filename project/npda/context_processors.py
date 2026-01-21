import re
from django.conf import settings
from django.core.cache import cache
from project.npda.general_functions.organisations_adapter import paediatric_diabetes_units_to_populate_select_field
from project.npda.models.banner import Banner
from project.npda.models.audit_period import AuditPeriod
from project.npda.views.npda_users import get_user_home_page


def get_audit_periods_user_can_see(user):
    audit_periods = []

    for audit_period in AuditPeriod.objects.order_by("start_date").all():
        if audit_period.is_visible or user.is_rcpch_audit_team_member or user.is_superuser:
            audit_periods.append(audit_period)
    
    return audit_periods


def context_from_request(request):
    # Permission checking done in @check_data_permissions or PDUPermissionMixin
    # We are fine to trust it here as this is for rendering purposes
    pz_code = None
    if request.resolver_match:
        pz_code = request.resolver_match.kwargs.get("pz_code", None)

    audit_period_slug = None
    if request.resolver_match and "audit_period" in request.resolver_match.kwargs:
        audit_period_slug = request.resolver_match.kwargs.get("audit_period", None)
    else:
        default_audit_period = AuditPeriod.objects.get_default_audit_period()
        audit_period_slug = default_audit_period.slug

    user_home_page = get_user_home_page(audit_period_slug, request.user)

    pdu_choices = paediatric_diabetes_units_to_populate_select_field(request.user) if request.user.is_authenticated else []
    audit_period_choices = get_audit_periods_user_can_see(request.user) if request.user.is_authenticated else []

    return {
        # Required for the url-data helper
        "pz_code": pz_code,
        "audit_period_slug": audit_period_slug,
        # Require for the nav
        "user_home_page": user_home_page,
        # Required for switcher
        "audit_period_choices": audit_period_choices,
        "pdu_choices": pdu_choices
    }


def context_from_settings(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "instance_label": settings.INSTANCE_LABEL
    }


def load_and_cache_banners():
    banners = cache.get("banner")

    if not banners:
        banners = Banner.objects.all()
        cache.set("banner", banners, timeout=10)
    
    return banners


def banner(request):
    banners = load_and_cache_banners()

    for banner in banners:
        url_matcher = re.compile(banner.url_matcher)

        if url_matcher.match(request.path) and not banner.disabled:
            if banner.user_role_to_target and request.user:
                if request.user.role == banner.user_role_to_target or request.user.is_rcpch_audit_team_member:
                    return { "banner": banner }
            elif not banner.user_role_to_target:
                return { "banner": banner }

    return {}
