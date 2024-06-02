# python imports
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# Logging setup
logger = logging.getLogger(__name__)


def login_and_otp_required():
    """
    Must have verified via 2FA
    """

    def decorator(view):
        # First use login_required on decorator
        login_required(view)

        def wrapper(request, *args, **kwargs):
            # Then, ensure 2fa verified
            user = request.user
            # Bypass 2fa if local dev, with warning message
            if settings.DEBUG and user.is_authenticated:
                logger.warning(
                    "User %s has bypassed 2FA for %s as settings.DEBUG is %s",
                    user,
                    view,
                    settings.DEBUG,
                )
                return view(request, *args, **kwargs)

            # Prevent unverified users
            if not user.is_verified():
                user_list = user.__dict__
                epilepsy12_user = user_list["_wrapped"]
                logger.info(
                    "User %s is unverified. Tried accessing %s",
                    epilepsy12_user,
                    view.__qualname__,
                )
                # raise PermissionDenied("Unverified user")
                return redirect("two_factor:login")

            return view(request, *args, **kwargs)

        return wrapper

    return decorator
