from datetime import datetime, timedelta
import logging

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils.html import strip_tags
from django.conf import settings
from two_factor.views import LoginView as TwoFactorLoginView


from ..models import NPDAUser, VisitActivity
from ..forms.npda_user_form import NPDAUserForm, CaptchaAuthenticationForm
from ..general_functions import (
    construct_confirm_email,
    send_email_to_recipients,
    construct_transfer_npda_site_email,
    construct_transfer_npda_site_outcome_email,
    group_for_role,
)
from .mixins import LoginAndOTPRequiredMixin
from django.utils.decorators import method_decorator
from .decorators import login_and_otp_required
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

"""
NPDAUser list and NPDAUser creation, deletion and update
"""


class NPDAUserListView(LoginAndOTPRequiredMixin, ListView):
    template_name = "npda_users.html"

    def get_queryset(self):
        return NPDAUser.objects.all().order_by("surname")


class NPDAUserCreateView(LoginAndOTPRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = NPDAUser
    form_class = NPDAUserForm
    # success_message = "New NPDA user created was created successfully"
    # success_url=reverse_lazy('npda_users')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New NPDA User"
        context["button_title"] = "Add NPDA User"
        context["form_method"] = "create"
        return context

    def form_valid(self, form):
        new_user = form.save(commit=False)
        new_user.set_unusable_password()
        new_user.is_active = True
        new_user.email_confirmed = False
        new_user.view_preference = 0
        try:
            new_user.save()
        except Exception as error:
            messages.error(
                self.request,
                f"Error: {error}. Account not created. Please contact the NPDA team if this issue persists.",
            )
            return redirect(
                "npda_users",
                # organisation_id=organisation_id,
            )

        new_group = group_for_role(new_user.role)

        try:
            new_user.groups.add(new_group)
        except Exception as error:
            messages.error(
                self.request,
                f"Error: {error}. Account not created. Please contact Epilepsy12 if this issue persists.",
            )
            return redirect(
                "npda_users",
                # organisation_id=organisation_id,
            )

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

        return redirect(
            "npda_users",
            # organisation_id=organisation_id,
        )

    def get_success_url(self) -> str:
        return reverse(
            "npda_users",
            # organisation_id=organisation_id,
        )


class NPDAUserUpdateView(LoginAndOTPRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Handle update of patient in audit
    """

    model = NPDAUser
    form_class = NPDAUserForm
    success_message = "NPDA User record updated successfully"
    success_url = reverse_lazy("npda_users")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit NPDA User Details"
        context["button_title"] = "Edit NPDA User Details"
        context["form_method"] = "update"
        context["npda_user"] = NPDAUser.objects.get(pk=self.kwargs["pk"])
        return context

    def is_valid(self):
        return super(NPDAUserForm, self).is_valid()

    def post(self, request: HttpRequest, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to resend email if recipient create account token has expired
        TODO: Only Superusers or Lead Clinicians can do this
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
        else:
            return super().post(request, *args, **kwargs)


class NPDAUserDeleteView(LoginAndOTPRequiredMixin, SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = NPDAUser
    success_message = "NPDA User removed from database"
    success_url = reverse_lazy("npda_users")


class NPDAUserLogsListView(LoginAndOTPRequiredMixin, ListView):
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


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
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
        self.request.user.password_last_set = timezone.now()

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
            request = self.request

            user = authenticate(
                request,
                username=request.POST.get("auth-username"),
                password=request.POST.get("auth-password"),
            )
            if user is not None:
                login(request, user)
                return redirect("home")

        # Otherwise, continue with usual workflow
        response = super().post(*args, **kwargs)
        return self.delete_cookies_from_response(response)

    # Override successful login redirect to org summary page
    def done(self, form_list, **kwargs):
        response = super().done(form_list)
        response_url = getattr(response, "url")
        login_redirect_url = reverse(settings.LOGIN_REDIRECT_URL)

        # Successful 2FA and login
        if response_url == login_redirect_url:
            user = self.get_user()
            """
            TODO - once organisations are implemented, this notifies the user on logging in that children have been transferred to their clinic
            """
            # if not user.organisation_employer:
            #     org_id = 1
            # else:
            #     org_id = user.organisation_employer.id
            #     # check for outstanding transfers in to this organisation
            #     if Site.objects.filter(
            #         active_transfer=True, organisation=user.organisation_employer
            #     ).exists() and user.has_perm(
            #         "epilepsy12.can_transfer_epilepsy12_lead_centre"
            #     ):
            #         # there is an outstanding request for transfer in to this user's organisation. User is a lead clinician and can act on this
            #         transfers = Site.objects.filter(
            #             active_transfer=True, organisation=user.organisation_employer
            #         )
            #         for transfer in transfers:
            #             messages.info(
            #                 self.request,
            #                 f"{transfer.transfer_origin_organisation} have requested transfer of {transfer.case} to {user.organisation_employer} for their Epilepsy12 care. Please find {transfer.case} in the case table to accept or decline this transfer request.",
            #             )

            # time since last set password
            delta = timezone.now() - user.password_last_set
            # if user has not renewed password in last 90 days, redirect to login page
            password_reset_date = user.password_last_set + timezone.timedelta(days=90)
            if user.is_active and (password_reset_date <= timezone.now()):
                messages.add_message(
                    request=self.request,
                    extra_tags=messages.ERROR,
                    message=f"Your password has expired. Please reset it.",
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

            return redirect(reverse("home"))
        return response
