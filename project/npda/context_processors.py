import re
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import SynchronousOnlyOperation

from project.npda.models import Banner
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


def can_alter_this_audit_year_submission(request):
    """
    This context processor is used to determine if the user can alter the submission for the current audit year.
    If the user is an admin, they can always alter the submission.
    If the user is not an admin, they can only alter the submission if the audit year is the current year.
    """
    if hasattr(request.user, "is_rcpch_audit_team_member"):
        if request.user.is_rcpch_audit_team_member:
            return {"can_alter_this_audit_year_submission": True}

    if (
        request.session.get("selected_audit_year") == get_current_audit_year()
        or request.user.is_superuser
    ):
        return {
            "can_alter_this_audit_year_submission": True,
        }
    else:
        return {"can_alter_this_audit_year_submission": False}


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


def site_contact_email(request):
    return settings.SITE_CONTACT_EMAIL


def load_and_cache_banners():
    banners = cache.get("banner")

    if not banners:
        banners = Banner.objects.all()
        cache.set("banner", banners, timeout=10)


def banner(request):
    banners = None

    

    for banner in banners:
        url_matcher = re.compile(banner.url_matcher)

        if url_matcher.match(request.path) and not banner.disabled:
            if banner.user_role_to_target and request.user:
                if request.user.role == banner.user_role_to_target or request.user.is_rcpch_audit_team_member:
                    return { "banner": banner }
            elif not banner.user_role_to_target:
                return { "banner": banner }

    return {}
