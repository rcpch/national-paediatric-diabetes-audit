"""Defines custom mixins used throughout our Class Based Views"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden

from ..general_functions.retrieve_pdu import retrieve_pdu_from_organisation_ods_code

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
        if settings.DEBUG and request.user.is_authenticated:
            logger.warning(
                "User %s has bypassed 2FA for %s as settings.DEBUG is %s and user has role %s and is superuser status: %s",
                request.user,
                self.__class__.__name__,
                settings.DEBUG,
                request.user.get_role_display(),
                request.user.is_superuser,
                # request.user.get_all_permissions(),
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


class CheckPDUMixin:
    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # get PDU assigned to user
        user_pdu = retrieve_pdu_from_organisation_ods_code(request.user.organisation_employer)['pz_code']

        # get pdu that user is requesting access of
        requested_pdu = request.session.get("sibling_organisations").get("pz_code")

        if request.user.is_superuser or (requested_pdu == user_pdu):
            return super().dispatch(request, *args, **kwargs)
        
        else:
            logger.info(
                    "User %s is unverified. Tried accessing %s but only has access to %s",
                    request.user,
                    requested_pdu,
                    user_pdu
                )
            raise PermissionDenied()
    
    def handle_no_permission(self):
        return HttpResponseForbidden("You do not have permission to access this PDU")