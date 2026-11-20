import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from project.npda.general_functions.entra_id import (
    ENTRA_ID_LOGIN_REQUIRED_MESSAGE,
    must_use_entra_id_login,
)
from project.npda.models import EntraIDDevice

logger = logging.getLogger(__name__)


class EntraIDLoginRequiredMiddleware:
    """
    When settings.ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF is True, end any
    session of a superuser or RCPCH Audit Team member that was not started by
    signing in with Microsoft Entra ID (for example one that began before the
    setting was switched on). Must come after django_otp's OTPMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ENTRA_ID_LOGIN_REQUIRED_FOR_RCPCH_STAFF:
            user = getattr(request, "user", None)
            if (
                user is not None
                and user.is_authenticated
                and must_use_entra_id_login(user)
                and not isinstance(getattr(user, "otp_device", None), EntraIDDevice)
            ):
                logger.info(
                    "Ending session for %s: must sign in with Entra ID", user.email
                )
                logout(request)

                # Let them carry on into the Entra ID sign in rather than
                # bouncing them back to the login page first
                if request.path in (
                    reverse("entra_id_login"),
                    reverse("entra_id_callback"),
                ):
                    return self.get_response(request)

                messages.warning(request, ENTRA_ID_LOGIN_REQUIRED_MESSAGE)
                login_url = resolve_url(settings.LOGIN_URL)

                # A redirect in reply to an htmx request would swap the login
                # page into part of the current page
                if getattr(request, "htmx", False):
                    return HttpResponseClientRedirect(login_url)

                return redirect(login_url)

        return self.get_response(request)
