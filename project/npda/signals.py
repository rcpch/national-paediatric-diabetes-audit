# python imports
import logging

# django imports
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.apps import apps

# RCPCH
from .models import VisitActivity, NPDAUser
from .general_functions.session import create_session_object

# Logging setup
logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Set up the session data so that views are filtered correctly (eg by PDU)
    # Default is to show all PDUs that the user has access to, including the PDU that the user is affiliated with
    new_session_object = create_session_object(user)
    request.session.update(new_session_object)

    logger.info(
        f"{user} ({user.email}) logged in from {get_client_ip(request)}. pz_code: {new_session_object['pz_code']}."
    )

    VisitActivity.objects.create(
        activity=1, ip_address=get_client_ip(request), npdauser=user
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, request, user=None, **kwargs):
    if user is not None:
        VisitActivity.objects.create(
            activity=2, ip_address=get_client_ip(request), npdauser=user
        )
        logger.info(
            f"{user} ({user.email}) failed log in from {get_client_ip(request)}."
        )
    elif "credentials" in kwargs:
        if NPDAUser.objects.filter(email=kwargs["credentials"]["username"]).exists():
            user = NPDAUser.objects.get(email=kwargs["credentials"]["username"])
            VisitActivity.objects.create(
                activity=2, ip_address=get_client_ip(request), npdauser=user
            )
            logger.info(
                f"{user} ({user.email}) failed log in from {get_client_ip(request)}."
            )
        else:
            logger.info("Login failure by unknown user")
    else:
        logger.info("Login failure by unknown user")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    logger.info(f"{user} ({user.email}) logged out from {get_client_ip(request)}.")
    VisitActivity.objects.create(
        activity=3, ip_address=get_client_ip(request), npdauser=user
    )


# helper functions
def get_client_ip(request):
    return request.META.get("REMOTE_ADDR")
