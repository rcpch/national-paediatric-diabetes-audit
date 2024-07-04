"""Defines custom mixins used throughout our Class Based Views"""

import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden

from project.npda.models.npda_user import NPDAUser
from project.npda.models.patient import Patient


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


class CheckPDUListMixin(AccessMixin):
    '''
    A mixin that checks whether a user can access a specific list view for a PDU
    '''
    def get_model(self):
        if hasattr(self, 'model') and self.model:
            return self.model
        if hasattr(self, 'get_queryset'):
            return self.get_queryset().model
        return None

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        model = self.get_model().__name__

        # get PDU assigned to user
        user_pdus = request.user.organisation_employers.values_list("pz_code")
        print(user_pdus)

        # get pdu that user is requesting access of
        requested_pdu = ""
        if model == "Visit":
            requested_patient = Patient.objects.get(pk=self.kwargs["patient_id"])
            requested_pdu = requested_patient.site.paediatric_diabetes_unit_pz_code
        
        elif model == "NPDAUser" or model == "Patient":
            requested_pdu = request.session.get("sibling_organisations").get("pz_code")

        if request.user.is_superuser or request.user.is_rcpch_audit_team_member or (requested_pdu in user_pdus):
            return super().dispatch(request, *args, **kwargs)
        
        else:
            logger.info(
                    "User %s is unverified. Tried accessing %s but only has access to %s",
                    request.user,
                    requested_pdu,
                    user_pdus
                )
            raise PermissionDenied()
    

class CheckPDUInstanceMixin(AccessMixin):
    '''
    A mixin which checks whether an instance's PDU (be it Patient, NPDAUser, Visit) that is having access attempted matches that of the 
    active user, or the active user is superuser/rcpch audit team
    '''
    def get_model(self):
        if hasattr(self, 'model') and self.model:
            return self.model
        if hasattr(self, 'get_queryset'):
            return self.get_queryset().model
        return None

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        model = self.get_model().__name__

        # get PDU assigned to user who is trying to access a view
        user_pdu = request.user.organisation_employers.first().pz_code

        # get pdu that user is requesting access of
        requested_pdu = ""

        if model == "NPDAUser":
            requested_user = NPDAUser.objects.get(pk=self.kwargs["pk"])
            requested_pdu =  requested_user.organisation_employers.first().pz_code
        
        elif model == "Patient":
            requested_patient = Patient.objects.get(pk=self.kwargs["pk"])
            requested_pdu = requested_patient.site.paediatric_diabetes_unit_pz_code
        
        elif model == "Visit":
            requested_patient = Patient.objects.get(pk=self.kwargs["patient_id"])
            requested_pdu = requested_patient.site.paediatric_diabetes_unit_pz_code

        if request.user.is_superuser or request.user.is_rcpch_audit_team_member or (requested_pdu == user_pdu):
            return super().dispatch(request, *args, **kwargs)
        
        else:
            logger.warning(
                    "User %s is unverified. Tried accessing %s but only has access to %s",
                    request.user,
                    requested_pdu,
                    user_pdu
                )
            raise PermissionDenied()