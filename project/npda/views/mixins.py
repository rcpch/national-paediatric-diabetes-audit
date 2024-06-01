"""Defines custom mixins used throughout our Class Based Views"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

logger = logging.getLogger(__name__)


class LoginAndOTPRequiredMixin(AccessMixin):
    """
    Mixin that ensures the user is logged in and has verified via OTP.

    Bypassed in local development is user.is_superuser AND settings.DEBUG==True.
    """

    def dispatch(self, request, *args, **kwargs):
        
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if the user is superuser and bypass 2FA in debug mode
        if settings.DEBUG and request.user.is_superuser:
            logger.warning(
                "User %s has bypassed 2FA for %s as settings.DEBUG is %s and user is superuser",
                request.user,
                self.__class__.__name__,
                settings.DEBUG,
            )
            return super().dispatch(request, *args, **kwargs)

        # Check if the user is verified
        if not request.user.is_verified():
            logger.info(
                "User %s is unverified. Tried accessing %s",
                request.user,
                self.__class__.__name__,
            )
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)
