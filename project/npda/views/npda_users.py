import logging
import unicodedata
from datetime import datetime, timedelta

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView
from django_otp import devices_for_user, user_has_device

# third party imports
from two_factor.views import LoginView as TwoFactorLoginView

from project.npda.filtersets.npdauser_filterset import NPDAUserFilterSet
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit

from ...constants import (
    AUDIT_CENTRE_COORDINATOR,
    AUDIT_CENTRE_EDITOR,
    AUDIT_CENTRE_READER,
    RCPCH_AUDIT_TEAM,
)
from ..forms.npda_user_form import CaptchaAuthenticationForm, NPDAUserForm
from ..general_functions import (
    construct_confirm_email,
    group_for_role,
    organisations_adapter,
    send_email_to_recipients,
)

# RCPCH imports
from ..models import AuditPeriod, NPDAUser, OrganisationEmployer, VisitActivity

# RCPCH imports
# RCPCH imports
from ..signals import get_client_ip
from .decorators import login_and_otp_required
from .mixins import LoginAndOTPRequiredMixin

# from ..signals import password_reset_sent

logger = logging.getLogger(__name__)


def _unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return (
        unicodedata.normalize("NFKC", s1).casefold()
        == unicodedata.normalize("NFKC", s2).casefold()
    )


def get_user_home_page(audit_period_slug, user):
    if not user.is_authenticated:
        return reverse("home")

    if (
        user.is_superuser
        or user.is_rcpch_audit_team_member
        or user.paediatric_diabetes_units.count() > 1
    ):
        return reverse("new-home", kwargs={"audit_period": audit_period_slug})

    return reverse(
        "pdu-dashboard",
        kwargs={
            "audit_period": audit_period_slug,
            "pz_code": user.primary_pdu().pz_code,
        },
    )


"""
NPDAUser list and NPDAUser creation, deletion and update
"""


class NPDAUserListView(LoginAndOTPRequiredMixin, PermissionRequiredMixin, FilterView):
    permission_required = "npda.view_npdauser"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    template_name = "npda_users.html"
    model = NPDAUser
    filterset_class = NPDAUserFilterSet
    context_object_name = "npdauser_list"

    def get_queryset(self):
        """
        Apply ordering
        """
        queryset = super().get_queryset()

        if not self.request.user.is_rcpch_audit_team_member:
            queryset = queryset.filter(
                organisation_employers__in=self.request.user.organisation_employers.all()
            )

        if "hide_users_other_than_test" in self.request.session.get(
            "feature_flags", []
        ):
            queryset = queryset.filter(email__icontains="test")

        queryset = queryset.order_by("-is_active", "surname")

        if self.request.user.is_rcpch_audit_team_member:
            # Distinct required to remove duplicates that come from the __in query
            queryset = queryset.distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "NPDA Users"
        return context

    def get(self, request, *args: str, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)

        if request.htmx:
            # filter the npdausers to only those in the same organisation as the user
            # trigger a GET request from the patient table to update the list of npdausers
            # by calling the get_queryset method again with the new ods_code/pz_code stored in session

            return render(
                request,
                "partials/npda_user_table.html",
                context=self.get_context_data(),
            )
        return response


class NPDAUserCreateView(
    LoginAndOTPRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    """
    Handle creation of new patient in audit
    """

    permission_required = "npda.add_npdauser"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."

    model = NPDAUser
    form_class = NPDAUserForm

    def get_form_kwargs(self):
        # add the request object to the form kwargs
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["employer_choices"] = (
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=self.request.user, user_instance=None
            )
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_rcpch_team"] = (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        )
        context["show_rcpch_staff_box"] = (
            self.request.user.is_superuser or self.request.user.is_rcpch_staff
        )
        context["title"] = "Add New NPDA User"
        context["button_title"] = "Add"
        context["form_method"] = "create"
        return context

    def form_valid(self, form):
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

        new_user_pz_code = (
            form.cleaned_data["add_employer"] or self.request.user.primary_pdu().pz_code
        )

        my_pz_codes = self.request.user.organisation_employers.values_list(
            "pz_code", flat=True
        )

        if new_user_pz_code not in my_pz_codes and not (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(
                f"You do not have permission to add users to {new_user_pz_code}. Contact the NPDA for assistance."
            )

        new_user_pdu = PaediatricDiabetesUnit.objects.get(pz_code=new_user_pz_code)

        if not new_user_pdu.active and not (
            self.request.user.is_rcpch_audit_team_member
            or self.request.user.is_superuser
        ):
            raise PermissionDenied(
                f"{new_user_pz_code} is inactive. Contact the NPDA for assistance."
            )

        if form.cleaned_data["role"] == RCPCH_AUDIT_TEAM and not (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(
                "You do not have permission to add a user with RCPCH Audit Team role."
            )

        if form.cleaned_data["is_rcpch_audit_team_member"] and not (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(
                "You do not have permission to add a user with the is_rcpch_audit_team_member flag."
            )

        if form.cleaned_data["is_rcpch_staff"] and not (
            self.request.user.is_superuser or self.request.user.is_rcpch_staff
        ):
            raise PermissionDenied(
                "You do not have permission to add a user with the is_rcpch_staff flag."
            )

        new_user = form.save(commit=False)
        new_user.set_unusable_password()
        new_user.is_active = True
        new_user.email_confirmed = False
        new_user.save()

        OrganisationEmployer.objects.create(
            paediatric_diabetes_unit=new_user_pdu,
            npda_user=new_user,
            is_primary_employer=True,
        )

        # add the user to the appropriate group
        new_group = group_for_role(new_user.role)
        new_user.groups.add(new_group)

        # user created - send email with reset link to new user
        subject = "Password Reset Requested"
        email = construct_confirm_email(request=self.request, user=new_user)

        send_email_to_recipients(
            recipients=[new_user.email], subject=subject, message=email
        )

        messages.success(
            self.request,
            f"Account created successfully. Confirmation email has been sent to {new_user.email}.",
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "npda_users",
        )


class NPDAUserUpdateView(
    LoginAndOTPRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    UpdateView,
):
    """
    Handle update of patient in audit
    """

    permission_required = "npda.view_npdauser"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."

    model = NPDAUser
    form_class = NPDAUserForm
    success_message = "NPDA User record updated successfully"
    success_url = reverse_lazy("npda_users")

    def user_in_exactly_the_same_pdus_as_requesting_user(self):
        my_pz_codes = set(
            self.request.user.organisation_employers.values_list("pz_code", flat=True)
        )
        their_pz_codes = set(
            self.get_object().organisation_employers.values_list("pz_code", flat=True)
        )

        return my_pz_codes == their_pz_codes

    def get_restricted_fields(self):
        if self.request.user.is_superuser:
            return []
        
        user_to_update = self.get_object()
        
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1449
        # A normal audit team member can't change the email of a superuser, preventing privilege escalation by changing the email
        # to one they control, resetting the password and 2fa then logging in.
        if self.request.user.is_rcpch_audit_team_member and not user_to_update.is_superuser:
            return []
        
        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1159
        # A coordinator can only change the role or email of a user if they share exactly the same PDU assignments
        # This prevents a coordinator accessing other PDUs by changing the email to one they control and doing a password reset
        if self.user_in_exactly_the_same_pdus_as_requesting_user() and not (user_to_update.is_superuser or user_to_update.is_rcpch_audit_team_member):
            return []

        # Default - restrict
        return ["role", "email"]

    def get_form_kwargs(self):
        # add the request object to the form kwargs
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        kwargs["employer_choices"] = (
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                # remove the edited users current employer from the list of employers in the drop down
                requesting_user=self.request.user,
                user_instance=self.get_object(),
            )
        )
        kwargs["restricted_fields"] = self.get_restricted_fields()

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = NPDAUser.objects.get(pk=self.kwargs["pk"])

        context["show_rcpch_team"] = (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        )
        context["show_rcpch_staff_box"] = (
            self.request.user.is_superuser or self.request.user.is_rcpch_staff
        )
        context["title"] = "Edit NPDA User Details"
        context["button_title"] = "Save"
        context["form_method"] = "update"
        context["npda_user"] = user
        context["organisation_employers"] = (
            OrganisationEmployer.objects.filter(npda_user=user)
            .all()
            .order_by("-is_primary_employer")
        )

        context["has_two_factor"] = user_has_device(user)

        two_factor_devices = devices_for_user(user)
        # The name doesn't describe the method used
        two_factor_devices = [
            f"{device.name} ({str(type(device).__name__)})"
            for device in two_factor_devices
        ]
        context["two_factor_devices"] = two_factor_devices

        return context

    def form_valid(self, form):
        if not self.request.user.has_perm("npda.change_npdauser"):
            raise PermissionDenied(
                "You do not have permission to edit this user. Contact the NPDA for assistance."
            )

        if form.cleaned_data["role"] == RCPCH_AUDIT_TEAM and not (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(
                "You do not have permission to grant the RCPCH Audit Team role."
            )

        if form.cleaned_data["is_rcpch_audit_team_member"] and not (
            self.request.user.is_superuser
            or self.request.user.is_rcpch_audit_team_member
        ):
            raise PermissionDenied(
                "You do not have permission to set the is_rcpch_audit_team_member flag."
            )

        if form.cleaned_data["is_rcpch_staff"] and not (
            self.request.user.is_superuser or self.request.user.is_rcpch_staff
        ):
            raise PermissionDenied(
                "You do not have permission to set the is_rcpch_staff flag."
            )

        changed_restricted_fields = [
            field
            for field in self.get_restricted_fields()
            if field in form.changed_data
        ]

        # https://github.com/rcpch/national-paediatric-diabetes-audit/issues/1159
        # A coordinator can only change the role or email of a user if they share exactly the same PDU assignments
        # This prevents a coordinator accessing other PDUs by changing the email to one they control and doing a password reset
        if len(changed_restricted_fields) > 0:
            # if the user is changing their role or email, they must be in the same PDU as the logged in user
            logger.warning(
                f"User {self.request.user.email} tried to change {', '.join(changed_restricted_fields)} of user {self.get_object().email} but they do not have exactly the same PDU assignments"
            )

            raise PermissionDenied(
                "You do not have permission to edit this user. Contact the NPDA for assistance."
            )

        user = form.save(commit=False)
        user.save()  # save the user first to ensure the user instance is updated and the updated_by and updated_at fields are set
        form.save_m2m()  # save the m2m fields (groups, employers, etc.)
        # remove all groups and add the user to the right group
        user.groups.clear()
        group = group_for_role(user.role)
        if group:
            user.groups.add(group)
        return super().form_valid(form)

    def post(self, request: HttpRequest, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to resend email if recipient create account token has expired
        TODO: Only Superusers or Coordinators can do this. Also the HTMX post request
        to update the employers list is handled here. The HTMX post request is not
        handled in the form_valid method as it is not a form submission.
        """
        if "resend_email" in request.POST:
            npda_user = NPDAUser.objects.get(pk=self.kwargs["pk"])
            subject = "Password Reset Requested"
            email = construct_confirm_email(request=request, user=npda_user)

            send_email_to_recipients(
                recipients=[npda_user.email],
                subject=subject,
                message=email,
            )

            messages.success(
                request,
                f"Confirmation and password reset request resent to {npda_user.email}.",
            )
            redirect_url = reverse(
                "npda_users",
            )
            return redirect(redirect_url)

        elif "activate" in request.POST or "deactivate" in request.POST:
            # A user can only be deactivated if they are not a superuser.
            # That of course can happen but for now we will only do this in the admin interface.
            npda_user = NPDAUser.objects.get(pk=self.kwargs["pk"])

            if npda_user == request.user:
                logger.warning(
                    "User %s is trying to activate/deactivate themselves", request.user
                )
                raise PermissionDenied()

            is_admin = (
                self.request.user.is_superuser
                or self.request.user.is_rcpch_audit_team_member
            )

            if not request.user.has_perm("npda.delete_npdauser") and not is_admin:
                logger.warning(
                    "User %s is trying to activate/deactivate user %s but does not have delete permission",
                    request.user.email,
                    npda_user.email,
                )
                raise PermissionDenied()

            if self.user_in_exactly_the_same_pdus_as_requesting_user() or is_admin:
                success_message = f"{npda_user.email} deactivated successfully."

                if "activate" in request.POST:
                    success_message = f"{npda_user.email} successfully reactivated."
                    npda_user.is_active = True
                else:
                    success_message = f"{npda_user.email} successfully deactivated."
                    npda_user.is_active = False

                npda_user.save()

                if "activate" in request.POST:
                    logger.info(
                        "User %s reactivated %s", request.user.email, npda_user.email
                    )
                else:
                    logger.warning(
                        "User %s deactivated %s", request.user.email, npda_user.email
                    )

                messages.success(request, success_message)
                return redirect(reverse("npda_users"))
            else:
                logger.warning(
                    "User %s is trying to activate/deactivate %s who is not in exactly the same PDUs as themselves",
                    request.user.email,
                    npda_user.email,
                )
                raise PermissionDenied()

        elif "reset-two-factor" in request.POST:
            if request.user.is_superuser or request.user.is_rcpch_audit_team_member:
                npda_user = NPDAUser.objects.get(pk=self.kwargs["pk"])

                if npda_user.is_superuser and not request.user.is_superuser:
                    logger.warning(
                        "User %s is trying to reset two-factor authentication for superuser %s",
                        request.user.email,
                        npda_user.email,
                    )
                    raise PermissionDenied(
                        "You do not have permission to reset two-factor authentication."
                    )

                devices = devices_for_user(user=npda_user)
                for device in devices:
                    device.delete()

                messages.success(
                    request,
                    f"Two-factor authentication reset for {npda_user.email}.",
                )
                redirect_url = reverse(
                    "npda_users",
                )
                return redirect(redirect_url)
            else:
                raise PermissionDenied(
                    "You do not have permission to reset two-factor authentication."
                )

        else:
            return super().post(request, *args, **kwargs)


@login_and_otp_required()
@permission_required("npda.can_transfer_npda_lead_centre", raise_exception=True)
def npdauser_pdu_update(request, pk):
    # Logic for updating the PDU for the NPDA user with the given pk
    # these are HTMX post requests from the edit user form
    # it is not called on submission of the form, only of the employers list
    # the return value is a partial view of the employers list, with the select, delete and set primary employer buttons
    template = "partials/pdu_user_affiliation_form.html"

    if not request.user.has_perm("npda.change_npdauser"):
        raise PermissionDenied(
            "You do not have permission to edit this user. Contact the NPDA for assistance."
        )

    selected_npda_user = NPDAUser.objects.get(pk=pk)
    if request.POST.get("update") == "delete":
        # delete the selected employer
        # cannot delete the primary employer but can set another employer as primary first and then delete the employer
        OrganisationEmployer.objects.filter(
            pk=request.POST.get("organisation_employer_id")
        ).delete()
        template = "partials/employers.html"
    elif request.POST.get("update") == "update":
        # set the selected employer as the primary employer. Reset all other employers to False before setting the selected employer to True since only one employer can be primary
        # set all employers to False
        template = "partials/employers.html"
        OrganisationEmployer.objects.filter(npda_user=selected_npda_user).update(
            is_primary_employer=False
        )
        # set the selected employer to True
        selected_employer = OrganisationEmployer.objects.filter(
            pk=request.POST.get("organisation_employer_id")
        ).get()
        selected_employer.is_primary_employer = True
        selected_employer.save()

    elif request.POST.get("add_employer"):
        template = "partials/employers.html"
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")
        # add to new employer to the users employer list after setting any existing employers is_primary_employer to False
        OrganisationEmployer.objects.filter(npda_user=selected_npda_user).update(
            is_primary_employer=False
        )
        # add the user to the appropriate organisation
        new_employer_pz_code = request.POST.get("add_employer")
        if new_employer_pz_code:
            my_pz_codes = request.user.organisation_employers.values_list(
                "pz_code", flat=True
            )

            if new_employer_pz_code not in my_pz_codes and not (
                request.user.is_superuser or request.user.is_rcpch_audit_team_member
            ):
                raise PermissionDenied(
                    f"You do not have permission to add users to {new_employer_pz_code}. Contact the NPDA for assistance."
                )

            # a new employer has been added
            selected_pdu = PaediatricDiabetesUnit.objects.get(
                pz_code=new_employer_pz_code
            )

            if not selected_pdu.active and not (
                request.user.is_rcpch_audit_team_member or request.user.is_superuser
            ):
                raise PermissionDenied(
                    f"{selected_pdu} is inactive. Contact the NPDA for assistance."
                )

            OrganisationEmployer.objects.update_or_create(
                paediatric_diabetes_unit=selected_pdu,
                npda_user=selected_npda_user,
                is_primary_employer=True,
            )

            selected_npda_user.refresh_from_db()

            # return the partial view of the employers list
            # if the a new employer has been added to the user, the new employer needs to be removed from the add_employer select list
            # the add_employer select list is repopulated with the remaining organisations - this happens by calling the get_form method

    return render(
        request=request,
        template_name=template,
        context={
            "npda_user": selected_npda_user,
            "organisation_employers": OrganisationEmployer.objects.filter(
                npda_user=selected_npda_user
            )
            .all()
            .order_by("-is_primary_employer"),
            "employer_choices": organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=request.user, user_instance=selected_npda_user
            ),
            "editable": request.user.has_perm("npda.change_npdauser"),
        },
    )


class NPDAUserLogsListView(LoginAndOTPRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "npda_user_logs.html"
    model = VisitActivity
    permission_required = "npda.view_visitactivity"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    paginate_by = 50
    context_object_name = "visitactivities"

    def get_queryset(self):
        npdauser_id = self.kwargs.get("npdauser_id")
        if not npdauser_id:
            logger.error("No NPDAUser ID provided in the request")
            return VisitActivity.objects.none()
        npdauser = NPDAUser.objects.get(pk=npdauser_id)
        return VisitActivity.objects.filter(npdauser=npdauser).order_by(
            "-activity_datetime"
        )

    def has_permission(self):
        """
        Custom permission check:
        - Readers and Editors can only view their own logs.
        - Coordinators can view logs for any user in their PDU.
        - RCPCH Audit Team can view logs for any user.
        """
        # Get the user whose logs are being viewed
        npdauser_id = self.kwargs.get("npdauser_id")
        if not npdauser_id:
            return False

        try:
            npda_user = NPDAUser.objects.get(pk=npdauser_id)
        except NPDAUser.DoesNotExist:
            return False

        # If user is a Reader or Editor, they can only see their own logs
        logged_in_user: NPDAUser = self.request.user
        is_reader_or_editor = logged_in_user.role in [
            AUDIT_CENTRE_READER,
            AUDIT_CENTRE_EDITOR,
        ]

        # Readers and Editors can only view their own logs
        if is_reader_or_editor and logged_in_user.pk != npda_user.pk:
            logger.warning(
                f"Reader or Editor user {logged_in_user.email} tried to view logs for another user {npda_user.email}"
            )
            return False

        # Coordinators can view logs for any user in their PDU
        if logged_in_user.role == AUDIT_CENTRE_COORDINATOR:
            try:
                npda_users_pdu_list = npda_user.organisation_employers.filter(
                    pz_code__in=logged_in_user.organisation_employers.all().values_list(
                        "pz_code", flat=True
                    ),
                )
            except PaediatricDiabetesUnit.DoesNotExist:
                logger.warning(f"Requested PDU for user {npda_user.email} not found")
                return False
            except Exception as e:
                logger.error(
                    f"Error getting requested PDU for user {npda_user.email}: {e}"
                )
                return False

            if not set(npda_user.organisation_employers.all()) & set(
                npda_users_pdu_list
            ):
                # if any of the user's employers are not in the logged in user's PDU list, deny access
                logger.warning(
                    f"Coordinator user {logged_in_user.email} tried to view logs for another user {npda_user.email} in a different PDU {npda_users_pdu_list}"
                )
                return False

        # RCPCH Audit Team can view logs for any user
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        npdauser_id = self.kwargs.get("npdauser_id")

        try:
            npdauser = NPDAUser.objects.get(pk=npdauser_id)
            context["npdauser"] = npdauser
        except NPDAUser.DoesNotExist:
            context["npdauser"] = None

        return context


"""
Authentication and password change
"""


class ResetPasswordForm(PasswordResetForm):
    def get_users(self, email):
        """Override Django's default behaviour to allow users with unusable passwords
        to reset their password, as that is how they are imported from CSV.
        """
        email_field_name = NPDAUser.get_email_field_name()
        active_users = NPDAUser._default_manager.filter(
            **{
                f"{email_field_name}__iexact": email,
                "is_active": True,
            }
        )
        return (
            u
            for u in active_users
            if _unicode_ci_compare(email, getattr(u, email_field_name))
        )


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    """
    Custom password reset view that sends a password reset email to the user
    """

    form_class = ResetPasswordForm
    template_name = "registration/password_reset.html"
    html_email_template_name = "registration/password_reset_email.html"
    email_template_name = strip_tags("registration/password_reset_email.html")
    subject_template_name = "registration/password_reset_subject.txt"
    success_message = (
        "We've emailed you instructions for setting your password, "
        "if an account exists with the email you entered. You should receive them shortly."
        " If you don't receive an email, "
        "please make sure you've entered the address you registered with, and check your spam folder."
    )
    extra_email_context = {
        "reset_password_link_expires_at": datetime.now()
        + timedelta(seconds=int(settings.PASSWORD_RESET_TIMEOUT))
    }
    success_url = reverse_lazy("login")

    # extend form_valid to set user.password_last_set
    def form_valid(self, form):
        # self.request.user.password_last_set = timezone.now()
        user_email_to_reset_password = form.cleaned_data["email"]
        # check if user exists
        if NPDAUser.objects.filter(email=user_email_to_reset_password).exists():
            user = NPDAUser.objects.get(email=user_email_to_reset_password)
            VisitActivity.objects.create(
                npdauser=user,
                activity=4,
                ip_address=get_client_ip(self.request),
            )  # password reset link sent
        return super().form_valid(form)


class RCPCHLoginView(TwoFactorLoginView):
    template_name = "two_factor/core/login.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override original Django Auth Form with Captcha field inserted
        self.form_list["auth"] = CaptchaAuthenticationForm

    def post(self, *args, **kwargs):
        # In local development, override the token workflow, just sign in
        # the user without 2FA token
        if settings.DEBUG:
            user = authenticate(
                self.request,
                username=self.request.POST.get("auth-username"),
                password=self.request.POST.get("auth-password"),
            )
            if user is not None:
                login(self.request, user)

                # Override normal auth flow behaviour, redirect straight away
                response = HttpResponseRedirect(self.get_success_url())
                return self._done(response, user)

        # Otherwise, continue with usual workflow
        response = super().post(*args, **kwargs)
        return self.delete_cookies_from_response(response)

    def get_success_url(self):
        if self.request.user:
            audit_period = AuditPeriod.objects.get_default_audit_period()
            return get_user_home_page(audit_period.slug, self.request.user)

        return reverse(settings.LOGIN_REDIRECT_URL)

    def _done(self, response, user):
        # time since last set password
        delta = timezone.now() - user.password_last_set
        # if user has not renewed password in last 90 days, redirect to login page
        password_reset_date = user.password_last_set + timezone.timedelta(days=90)
        if (
            user.is_active
            and (password_reset_date <= timezone.now())
            and user.is_superuser is False
        ):
            messages.add_message(
                self.request,
                messages.ERROR,
                "Your password has expired. Please reset it.",
            )
            return redirect(reverse("password_reset"))

        last_logged_in = VisitActivity.objects.filter(
            activity=1, npdauser=user
        ).order_by("-activity_datetime")[:2]
        if last_logged_in.count() > 1:
            messages.add_message(
                self.request,
                messages.INFO,
                f"You are now logged in as {user.email}. You last logged in at {timezone.localtime(last_logged_in[1].activity_datetime).strftime('%H:%M %p on %A, %d %B %Y')} from {last_logged_in[1].ip_address}.\nYou have {90 - delta.days} days remaining until your password needs resetting.",
            )
        else:
            messages.add_message(
                self.request,
                messages.INFO,
                f"You are now logged in as {user.email}. Welcome to the National Paediatric Diabetes Audit platform! This is your first time logging in ({timezone.localtime(last_logged_in[0].activity_datetime).strftime('%H:%M %p on %A, %d %B %Y')} from {last_logged_in[0].ip_address}).",
            )

        return response

    def done(self, form_list, **kwargs):
        response = super().done(form_list)
        return self._done(response, self.get_user())
