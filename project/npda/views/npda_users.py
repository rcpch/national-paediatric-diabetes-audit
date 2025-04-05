from datetime import datetime, timedelta
import logging
import unicodedata

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView

# third party imports
from two_factor.views import LoginView as TwoFactorLoginView

# RCPCH imports
from ..models import (
    NPDAUser,
    VisitActivity,
    OrganisationEmployer,
)
from ..forms.npda_user_form import NPDAUserForm, CaptchaAuthenticationForm
from ..general_functions import (
    construct_confirm_email,
    send_email_to_recipients,
    group_for_role,
    organisations_adapter,
)
from .mixins import CheckPDUInstanceMixin, CheckPDUListMixin, LoginAndOTPRequiredMixin
from .mixins import LoginAndOTPRequiredMixin
from ...constants import RCPCH_AUDIT_TEAM

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


"""
NPDAUser list and NPDAUser creation, deletion and update
"""


class NPDAUserListView(
    LoginAndOTPRequiredMixin, CheckPDUListMixin, PermissionRequiredMixin, ListView
):
    permission_required = "npda.view_npdauser"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."
    template_name = "npda_users.html"

    def get_queryset(self):
        # scope the queryset to filter only those users in organisations in the same PDU. This is to prevent users from seeing all users in the system
        pz_code = self.request.session.get("pz_code")
        flag_field = Count("organisation_employers")

        if self.request.user.viewing_data_nationally():
            return (
                NPDAUser.objects.all()
                .annotate(number_of_pdu_memberships=flag_field)
                .order_by("surname")
            )

        return (
            NPDAUser.objects.filter(organisation_employers__pz_code=pz_code)
            .annotate(number_of_pdu_memberships=flag_field)
            .order_by("surname")
        )

    def get_context_data(self, **kwargs):
        context = super(NPDAUserListView, self).get_context_data(**kwargs)
        context["title"] = "NPDA Users"
        context["pz_code"] = self.request.session.get("pz_code")
        context["pdu_choices"] = (
            organisations_adapter.paediatric_diabetes_units_to_populate_select_field(  # This is used to populate the select field in view preference form
                requesting_user=self.request.user, user_instance=self.request.user
            )
        )
        context["chosen_pdu"] = self.request.session.get("pz_code")
        return context

    def get(self, request, *args: str, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)

        if request.htmx:
            # filter the npdausers to only those in the same organisation as the user
            # trigger a GET request from the patient table to update the list of npdausers
            # by calling the get_queryset method again with the new ods_code/pz_code stored in session
            queryset = self.get_queryset()
            context = self.get_context_data()
            context["npdauser_list"] = queryset

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
        context["selected_pdu"] = self.request.session.get("pz_code")
        return context

    def form_valid(self, form):
        PaediatricDiabetesUnit = apps.get_model("npda", "PaediatricDiabetesUnit")

        new_user_pz_code = form.cleaned_data["add_employer"] or self.request.session.get("pz_code")

        my_pz_codes = self.request.user.organisation_employers.values_list("pz_code", flat=True)

        if new_user_pz_code not in my_pz_codes and not (self.request.user.is_superuser or self.request.user.is_rcpch_audit_team_member):
            raise PermissionDenied(
                f"You do not have permission to add users to {new_user_pz_code}. Contact the NPDA for assistance."
            )
        
        new_user_pdu = PaediatricDiabetesUnit.objects.get(pz_code=new_user_pz_code)

        if not new_user_pdu.active and not (self.request.user.is_rcpch_audit_team_member or self.request.user.is_superuser):
            raise PermissionDenied(
                f"{new_user_pz_code} is inactive. Contact the NPDA for assistance."
            )
        
        if form.cleaned_data["role"] == RCPCH_AUDIT_TEAM and not (self.request.user.is_superuser or self.request.user.is_rcpch_audit_team_member):
            raise PermissionDenied(
                "You do not have permission to add a user with RCPCH Audit Team role."
            )

        new_user = form.save(commit=False)
        new_user.set_unusable_password()
        new_user.is_active = True
        new_user.email_confirmed = False
        new_user.view_preference = 1  # PDU level view preference
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
    CheckPDUInstanceMixin,
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
        context["title"] = "Edit NPDA User Details"
        context["button_title"] = "Save"
        context["form_method"] = "update"
        context["npda_user"] = NPDAUser.objects.get(pk=self.kwargs["pk"])
        context["organisation_employers"] = (
            OrganisationEmployer.objects.filter(npda_user=context["npda_user"])
            .all()
            .order_by("-is_primary_employer")
        )
        return context

    def form_valid(self, form):
        if not self.request.user.has_perm("npda.change_npdauser"):
            raise PermissionDenied(
                "You do not have permission to edit this user. Contact the NPDA for assistance."
            )
        
        if form.cleaned_data["role"] == RCPCH_AUDIT_TEAM and not (self.request.user.is_superuser or self.request.user.is_rcpch_audit_team_member):
            raise PermissionDenied(
                "You do not have permission to add a user with RCPCH Audit Team role."
            )
        
        user = form.save(commit=True)
        # remove all groups and add the user to the right group
        user.groups.clear()
        group = group_for_role(user.role)
        if group:
            user.groups.add(group)
        return super().form_valid(form)

    def post(self, request: HttpRequest, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to resend email if recipient create account token has expired
        TODO: Only Superusers or Coordinators can do this
        """
        if request.htmx:
            # these are HTMX post requests from the edit user form
            # it is not called on submission of the form, only of the employers list
            # the return value is a partial view of the employers list, with the select, delete and set primary employer buttons

            if not request.user.has_perm("npda.change_npdauser"):
                raise PermissionDenied(
                    "You do not have permission to edit this user. Contact the NPDA for assistance."
                )

            selected_npda_user = NPDAUser.objects.get(pk=self.kwargs["pk"])
            if request.POST.get("update") == "delete":
                # delete the selected employer
                # cannot delete the primary employer but can set another employer as primary first and then delete the employer
                OrganisationEmployer.objects.filter(
                    pk=request.POST.get("organisation_employer_id")
                ).delete()
            elif request.POST.get("update") == "update":
                # set the selected employer as the primary employer. Reset all other employers to False before setting the selected employer to True since only one employer can be primary
                # set all employers to False
                OrganisationEmployer.objects.filter(
                    npda_user=selected_npda_user
                ).update(is_primary_employer=False)
                # set the selected employer to True
                OrganisationEmployer.objects.filter(
                    pk=request.POST.get("organisation_employer_id")
                ).update(is_primary_employer=True)

            elif request.POST.get("add_employer"):
                PaediatricDiabetesUnit = apps.get_model(
                    "npda", "PaediatricDiabetesUnit"
                )
                # add to new employer to the users employer list after setting any existing employers is_primary_employer to False
                OrganisationEmployer.objects.filter(
                    npda_user=selected_npda_user
                ).update(is_primary_employer=False)
                # add the user to the appropriate organisation
                new_employer_pz_code = request.POST.get("add_employer")
                if new_employer_pz_code:
                    my_pz_codes = self.request.user.organisation_employers.values_list("pz_code", flat=True)

                    if new_employer_pz_code not in my_pz_codes and not (self.request.user.is_superuser or self.request.user.is_rcpch_audit_team_member):
                        raise PermissionDenied(
                            f"You do not have permission to add users to {new_employer_pz_code}. Contact the NPDA for assistance."
                        )

                    # a new employer has been added
                    selected_pdu = PaediatricDiabetesUnit.objects.get(
                        pz_code=new_employer_pz_code
                    )

                    if not selected_pdu.active and not (self.request.user.is_rcpch_audit_team_member or self.request.user.is_superuser):
                        raise PermissionDenied(
                            f"{new_user_pz_code} is inactive. Contact the NPDA for assistance."
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

            # get the user being edited
            user_instance = self.get_object()

            organisation_choices = organisations_adapter.paediatric_diabetes_units_to_populate_select_field(
                requesting_user=self.request.user, user_instance=user_instance
            )

            return render(
                request=request,
                template_name="partials/employers.html",
                context={
                    "npda_user": selected_npda_user,
                    "organisation_employers": OrganisationEmployer.objects.filter(
                        npda_user=selected_npda_user
                    )
                    .all()
                    .order_by("-is_primary_employer"),
                    "organisation_choices": organisation_choices,
                },
            )
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
        else:
            return super().post(request, *args, **kwargs)

        


class NPDAUserDeleteView(
    LoginAndOTPRequiredMixin,
    CheckPDUInstanceMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    DeleteView,
):
    """
    Handle deletion of user from audit
    """

    permission_required = "npda.delete_npdauser"
    permission_denied_message = "You do not have the appropriate permissions to access this page/feature. Contact your Coordinator for assistance."

    model = NPDAUser
    success_message = "NPDA User removed from database"
    success_url = reverse_lazy("npda_users")


class NPDAUserLogsListView(LoginAndOTPRequiredMixin, CheckPDUInstanceMixin, ListView):
    template_name = "npda_user_logs.html"
    model = VisitActivity

    def get_context_data(self, **kwargs):
        npdauser_id = self.kwargs.get("npdauser_id")
        context = super(NPDAUserLogsListView, self).get_context_data(**kwargs)
        npdauser = NPDAUser.objects.get(pk=npdauser_id)
        visitactivities = VisitActivity.objects.filter(npdauser=npdauser)
        context["visitactivities"] = visitactivities
        context["npdauser"] = npdauser
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
                "%s__iexact" % email_field_name: email,
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
                ip_address=self.request.META.get("REMOTE_ADDR"),
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
                # successful login, get PDU and organisation details from user and store in session

                # Override normal auth flow behaviour, redirect straight to home page
                return redirect("dashboard")

        # Otherwise, continue with usual workflow
        response = super().post(*args, **kwargs)
        return self.delete_cookies_from_response(response)

    # Override successful login redirect to org summary page
    def done(self, form_list, **kwargs):
        # this will not be called if debug=True
        response = super().done(form_list)
        response_url = getattr(response, "url")

        # redirect to home page
        login_redirect_url = reverse(settings.LOGIN_REDIRECT_URL)

        # Successful 2FA and login
        if response_url == login_redirect_url:
            user = self.get_user()

            # time since last set password
            delta = timezone.now() - user.password_last_set
            # if user has not renewed password in last 90 days, redirect to login page
            password_reset_date = user.password_last_set + timezone.timedelta(days=90)
            if user.is_active and (password_reset_date <= timezone.now()):
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    f"Your password has expired. Please reset it.",
                )
                return redirect(reverse("password_reset"))

            last_logged_in = VisitActivity.objects.filter(
                activity=1, npdauser=user
            ).order_by("-activity_datetime")[:2]
            if last_logged_in.count() > 1:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    f"You are now logged in as {user.email}. You last logged in at {timezone.localtime(last_logged_in[1].activity_datetime).strftime('%H:%M %p on %A, %d %B %Y')} from {last_logged_in[1].ip_address}.\nYou have {90-delta.days} days remaining until your password needs resetting.",
                )
            else:
                messages.add_message(
                    self.request,
                    messages.INFO,
                    f"You are now logged in as {user.email}. Welcome to the National Paediatric Diabetes Audit platform! This is your first time logging in ({timezone.localtime(last_logged_in[0].activity_datetime).strftime('%H:%M %p on %A, %d %B %Y')} from {last_logged_in[0].ip_address}).",
                )

            return redirect(reverse("dashboard"))
        return response
