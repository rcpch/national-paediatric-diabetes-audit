import re
from django.conf import settings
from django.core.cache import cache
from project.npda.models.banner import Banner
from project.npda.views.npda_users import get_user_home_page

def current_pz_code(request):
    pz_code = None

    if request.resolver_match:
        pz_code = request.resolver_match.kwargs.get("pz_code", None)

    if not pz_code:
        pz_code = request.session.get("pz_code", None)

    return pz_code

def current_audit_period_slug(request):
    audit_period_slug = None

    if request.resolver_match:
        audit_period_slug = request.resolver_match.kwargs.get("audit_period", None)

    # Temporary hack until all pages migrated over to new URL structure
    if not audit_period_slug:
        audit_year = request.session.get("selected_audit_year", None)

        if audit_year:
            audit_period_slug = f"{audit_year}-{audit_year + 1}"

    return audit_period_slug

# Temporary hack until switcher removed so you can only change audit period by following links
def current_audit_year(audit_period_slug):
    if audit_period_slug:
        start_year = int(audit_period_slug.split("-")[0])
        return start_year
    
    return None


def session_data(request):
    # Permission checking done in @check_data_permissions or PDUPermissionMixin
    # We are fine to trust it here as this is for rendering purposes
    pz_code = current_pz_code(request)
    audit_period_slug = current_audit_period_slug(request)
    user_home_page = get_user_home_page(audit_period_slug, request.user)

    return {
        # Required for the url-data helper
        "pz_code": pz_code,
        "audit_period_slug": audit_period_slug,
        "audit_years": request.session.get("audit_years", []),
        # Required for switcher
        "selected_audit_year": current_audit_year(audit_period_slug),
        "user_home_page": user_home_page
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
