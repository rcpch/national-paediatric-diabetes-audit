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
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models.transfer import Transfer
from project.npda.models.submission import Submission
from django.urls import reverse


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


class PDUPermissionMixin(AccessMixin):
    def data_reverse(self, viewname, kwargs={}):
        next_kwargs = kwargs | {
            "audit_period": self.audit_period.slug,
            "pz_code": self.pdu.pz_code
        }

        return reverse(viewname, kwargs=next_kwargs)

    def get_model(self):
        if hasattr(self, "model") and self.model:
            return self.model
        if hasattr(self, "get_queryset"):
            return self.get_queryset().model
        return None

    def check_patient_permissions(self, pdu, audit_period, user, pk):
        patient = get_object_or_404(Patient, pk=pk)
        transfer = Transfer.objects.get(patient=patient)

        if not transfer.paediatric_diabetes_unit in user.organisation_employers.all():
            raise PermissionDenied(f"User {user} does not have permission to view patient for PDU {pdu.pz_code} in audit period {audit_period.slug}")

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        audit_period = AuditPeriod.objects.get_audit_period_for_request(request, *args, **kwargs)
        pdu = PaediatricDiabetesUnit.objects.get_pdu_for_request(request, *args, **kwargs)

        model = self.get_model().__name__

        if not request.user.is_superuser and not request.user.is_rcpch_audit_team_member:
            match model:
                # PDU level permission checked in the request helpers above. This is to prevent access to models by guessing their pk.
                case "Patient" if "pk" in self.kwargs:
                    self.check_patient_permissions(pdu, audit_period, request.user, self.kwargs["pk"])

                case "Visit":
                    self.check_patient_permissions(pdu, audit_period, request.user, self.kwargs["patient_id"])

                # PDU level permission checked in the request helpers above. This is to prevent access to models by guessing their pk.
                case "NPDAUser" if "pk" in self.kwargs:
                    requested_user = get_object_or_404(NPDAUser, pk=self.kwargs['pk'])
                    if not requested_user.organisation_employers.filter(pz_code=pdu.pz_code).exists():
                        raise PermissionDenied(f"User {request.user} does not have permission to view {model} for PDU {pdu.pz_code} in audit period {audit_period.slug}")

        self.audit_period = audit_period
        self.pdu = pdu

        return super().dispatch(request, *args, **kwargs)


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


class QuestionnaireContextMixin(AccessMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)
        pdu = PaediatricDiabetesUnit.objects.get_pdu_for_request(self.request)

        submission = Submission.objects.get_submission_for_request(pdu, audit_period)

        is_csv_upload = submission and submission.csv_file_name is not None
        is_questionnaire = not is_csv_upload if submission else True

        can_override_data_upload_rules = self.request.user.is_superuser or getattr(self.request.user, "is_rcpch_audit_team_member", False)
        data_upload_rules_overridden = can_override_data_upload_rules and self.request.GET.get("unlock", False)
        
        return context | {
            "is_csv_upload": is_csv_upload,
            "is_questionnaire": is_questionnaire,
            "can_override_data_upload_rules": can_override_data_upload_rules,
            "data_upload_rules_overridden": data_upload_rules_overridden,
            "can_use_questionnaire": data_upload_rules_overridden or is_questionnaire,
        }  


class CheckCanCompleteQuestionnaireMixin(QuestionnaireContextMixin, AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        # Overriding data upload rules just applies in the UI
        if request.user.is_superuser or request.user.is_rcpch_audit_team_member:
            return super().dispatch(request, *args, **kwargs)

        if request.method != "GET":
            audit_period = AuditPeriod.objects.get_audit_period_for_request(self.request)
            pdu = PaediatricDiabetesUnit.objects.get_pdu_for_request(self.request)

            submission = Submission.objects.get_submission_for_request(pdu, audit_period)
            is_questionnaire = not submission.csv_file_name if submission else True

            if not is_questionnaire:
                logger.warning(
                    f"User {request.user} tried to complete the questionnaire for a CSV upload submission."
                )
                raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)