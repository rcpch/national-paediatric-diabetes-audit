"""Defines custom mixins used throughout our Class Based Views"""

from datetime import datetime
import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import get_object_or_404

from project.npda.models.npda_user import NPDAUser
from project.npda.models.patient import Patient
from project.npda.models.audit_period import AuditPeriod


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
    """
    A mixin that checks whether a user can access a specific list view for a PDU
    """

    def get_model(self):
        if hasattr(self, "model") and self.model:
            return self.model
        if hasattr(self, "get_queryset"):
            return self.get_queryset().model
        return None

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        model = self.get_model().__name__

        # get PDU assigned to user
        user_pdus = request.user.organisation_employers.values_list(
            "pz_code", flat=True
        )

        # get pdu that user is requesting access of
        requested_pdu = ""
        if model == "Visit":
            requested_patient = get_object_or_404(Patient, pk=self.kwargs["patient_id"])
            Transfer = apps.get_model("npda", "Transfer")
            transfer = Transfer.objects.get(patient=requested_patient)
            requested_pdu = transfer.paediatric_diabetes_unit.pz_code

        elif model == "NPDAUser" or model == "Patient":
            requested_pdu = request.session.get("pz_code")

        if (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or (requested_pdu in user_pdus)
        ):
            return super().dispatch(request, *args, **kwargs)

        else:
            logger.info(
                "User %s is unverified. Tried accessing %s but only has access to %s",
                request.user,
                requested_pdu,
                user_pdus,
            )
            raise PermissionDenied()


class CheckPDUInstanceMixin(AccessMixin):
    """
    A mixin which checks whether an instance's PDU (be it Patient, NPDAUser, Visit) that is having access attempted matches that of the
    active user, or the active user is superuser/rcpch audit team
    """

    def get_model(self):
        if hasattr(self, "model") and self.model:
            return self.model
        if hasattr(self, "get_queryset"):
            return self.get_queryset().model
        return None

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        model = self.get_model().__name__

        Transfer = apps.get_model("npda", "Transfer")

        # get PDUs assigned to user who is trying to access a view
        user_pdus = [org.pz_code for org in request.user.organisation_employers.all()]

        if model == "NPDAUser":
            requested_user = get_object_or_404(NPDAUser, pk=self.kwargs['pk'])
            if requested_user.organisation_employers.filter(pz_code=request.session.get('pz_code')).exists():
                if requested_user.number_of_pdu_memberships() == 1:
                    # if the user is a member of the requested pdu and there is only one, then we can use that
                    requested_pdu = requested_user.organisation_employers.all().filter(pz_code=request.session.get('pz_code')).first().pz_code
                else:
                    # if the user is a member of multiple PDUs, then we need to check which one they are trying to access
                    requested_pdu = requested_user.organisation_employers.all().filter(pz_code=request.session.get('pz_code')).first().pz_code
            else:
                # the user is not a member of the requested pdu so we just return the pz code of the users primary pdu
                requested_pdu = requested_user.paediatric_diabetes_units.filter(is_primary_employer=True).first().paediatric_diabetes_unit.pz_code


        elif model == "Patient":
            requested_patient = get_object_or_404(Patient, pk=self.kwargs["pk"])
            transfer = Transfer.objects.get(patient=requested_patient)
            requested_pdu = transfer.paediatric_diabetes_unit.pz_code

        elif model == "Visit":
            requested_patient = get_object_or_404(Patient, pk=self.kwargs["patient_id"])
            transfer = Transfer.objects.get(patient=requested_patient)
            requested_pdu = transfer.paediatric_diabetes_unit.pz_code

        if('activate' in request.POST or 'deactivate' in request.POST):
            # If the user is trying to activate or deactivate a user, we need to check if they are allowed to do so
            # This is only allowed if they have delete permissions for the user model, are in the same PDU (if not a superuser or audit team member or RCPCH staff), and the user is not in multiple PDUs
            # Finally, they must not be trying to activate/deactivate themselves
            if request.user.pk == int(self.kwargs.get('pk', 0)):
                # If the user is trying to activate/deactivate themselves, we deny access
                logger.warning(
                    "User %s is trying to activate/deactivate themselves with PDU %s",
                    request.user,
                    requested_pdu,
                )
                raise PermissionDenied()
            if request.user.has_perm('npda.delete_npdauser'):
                # If the user has delete permissions, they can activate or deactivate users, so long as they are in the same PDU and the user is not in multiple PDUs, or 
                # they are a superuser or audit team member or rcpch staff and the user is not in multiple PDUs
                requested_user = get_object_or_404(NPDAUser, pk=self.kwargs['pk'])
                if (requested_pdu in user_pdus and requested_user.organisation_employers.count() == 1) or (request.user.is_superuser or request.user.is_rcpch_audit_team_member or request.user.is_rcpch_staff):
                    logger.info(
                        "User %s is trying to activate/deactivate a user with PDU %s",
                        request.user,
                        requested_pdu,
                    )
                    # Allow access to the view
                    return super().dispatch(request, *args, **kwargs)
                else:
                    # User is trying to activate/deactivate a user with multiple PDUs, but they are not a superuser or audit team member
                    logger.warning(
                        "User %s is trying to activate/deactivate a user with PDU %s but does not have the correct permissions",
                        request.user,
                        requested_pdu,
                    )
                    # If they are not a superuser or audit team member, deny access
                    raise PermissionDenied()
            else:
                # No permissions: You shall not pass! 🧙🏻‍♂️
                logger.warning(
                    "User %s is trying to activate/deactivate a user with PDU %s but does not have delete permissions",
                    request.user,
                    requested_pdu,
                )
                # If they are not a superuser or audit team member, deny access
                raise PermissionDenied()
        elif (
            request.user.is_superuser
            or request.user.is_rcpch_audit_team_member
            or (requested_pdu in user_pdus)
        ):
            return super().dispatch(request, *args, **kwargs)
            
        else:
            logger.warning(
                "User %s is unverified. Tried accessing %s but only has access to %s",
                request.user,
                requested_pdu,
                user_pdus,
            )
            raise PermissionDenied()


class CheckCurrentAuditYearMixin(AccessMixin):
    """
    A mixin that checks whether the user is trying to update/create or delete data for an open audit year
    If trying to access data for a different audit year, it will log a warning and return a HttpResponseForbidden
    """

    def dispatch(self, request, *args, **kwargs):
        audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)
        
        if not audit_period:
            logger.warning(
                f"User {request.user} tried to create/edit or delete data in an unknown audit period."
            )
            raise PermissionDenied()
        
        if not audit_period.is_open:
            if not request.user.is_superuser and not request.user.is_rcpch_audit_team_member:
                logger.warning(
                    f"User {request.user} tried to create/edit or delete data in a closed audit year."
                )
                raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)


class CheckCanCompleteQuestionnaireMixin(AccessMixin):
    """
    A mixin that checks whether the user can complete the questionnaire:
      - The submission is not a CSV upload (can_complete_questionnaire = True)
      - The submission is not a CSV upload
        - and the operation is a GET (the UI has code to display read only)
        - or you are a superuser or audit team member
    
    It also returns context data for templates to conditionally render UI based on the type of upload.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)

        session_is_audit_year_open = audit_period and audit_period.is_open
        session_can_upload_csv = self.request.session.get("can_upload_csv", True)
        session_can_use_questionnaire = self.request.session.get("can_complete_questionnaire", True)

        can_override_data_upload_rules = self.request.user.is_superuser or getattr(self.request.user, "is_rcpch_audit_team_member", False)
        data_upload_rules_overridden = can_override_data_upload_rules and self.request.GET.get("unlock", False)

        return context | {
            "is_csv_upload": session_can_upload_csv,
            "is_questionnaire": session_can_use_questionnaire,
            "can_override_data_upload_rules": can_override_data_upload_rules,
            "data_upload_rules_overridden": data_upload_rules_overridden,
            "can_use_questionnaire": data_upload_rules_overridden or (session_is_audit_year_open and session_can_use_questionnaire),
        }

    def dispatch(self, request, *args, **kwargs):
        # Check if the user has the permission to complete the questionnaire
        if not request.session.get("can_complete_questionnaire"):
            if request.method == "GET" or request.user.is_superuser or request.user.is_rcpch_audit_team_member:
                # Allow superusers and RCPCH audit team members to complete the questionnaire
                return super().dispatch(request, *args, **kwargs)

            logger.warning(
                f"User {request.user} tried to complete the questionnaire without the permission to do so."
            )
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)
