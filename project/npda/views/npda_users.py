import json
from datetime import datetime, timedelta
import logging

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.shortcuts import redirect, render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse, reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils.html import strip_tags
from django.conf import settings

# third party imports
from two_factor.views import LoginView as TwoFactorLoginView
from django_htmx.http import trigger_client_event

# RCPCH imports
from project.npda.general_functions.rcpch_nhs_organisations import (
    get_all_nhs_organisations,
)
from project.npda.general_functions.retrieve_pdu import retrieve_pdu, retrieve_pdu_list


from ..models import NPDAUser, VisitActivity, OrganisationEmployer
from ..forms.npda_user_form import NPDAUserForm, CaptchaAuthenticationForm
from ..general_functions import (
    construct_confirm_email,
    send_email_to_recipients,
    group_for_role,
    retrieve_pdu_from_organisation_ods_code,
)
from .mixins import LoginAndOTPRequiredMixin

logger = logging.getLogger(__name__)

"""
NPDAUser list and NPDAUser creation, deletion and update
"""


class NPDAUserListView(LoginAndOTPRequiredMixin, ListView):
    template_name = "npda_users.html"

    def get_queryset(self):
        # scope the queryset to filter only those users in organisations in the same PDU. This is to prevent users from seeing all users in the system
        # The user's organisation, PDU and siblings are stored in the session when they log in

        if self.request.user.view_preference == 1:
            # PDU view
            # create a list of sibling organisations' ODS codes who share the same PDU as the user
            siblings_ods_codes = [
                sibling["ods_code"]
                for sibling in self.request.session["sibling_organisations"][
                    "organisations"
                ]
            ]
            # get all users in the sibling organisations
            return (
                NPDAUser.objects.filter(
                    organisation_employer__ods_code__in=siblings_ods_codes
                )
                .distinct()
                .order_by("surname")
            )
        elif self.request.user.view_preference == 2:
            # RCPCH user/national view - get all users
            return NPDAUser.objects.all().order_by("surname")
        else:
            raise ValueError("Invalid view preference")

    def get_context_data(self, **kwargs):
        context = super(NPDAUserListView, self).get_context_data(**kwargs)
        context["title"] = "NPDA Users"
        pz_code = self.request.session.get("sibling_organisations", {}).get(
            "pz_code", None
        )
        context["pz_code"] = pz_code
        context["ods_code"] = self.request.session.get("ods_code")
        context["organisation_choices"] = self.request.session.get(
            "organisation_choices"
        )
        context["pdu_choices"] = self.request.session.get("pdu_choices")
        context["chosen_pdu"] = self.request.session.get("sibling_organisations").get(
            "pz_code"
        )
        return context

    def get(self, request, *args: str, **kwargs) -> HttpResponse:
        response = super().get(request, *args, **kwargs)
        if request.htmx:
            # filter the npdausers to only those in the same organisation as the user
            # trigger a GET request from the patient table to update the list of npdausers
            # by calling the get_queryset method again with the new ods_code/pz_code stored in session
            logger.warning("HTMX request received")
            queryset = self.get_queryset()
            context = self.get_context_data()
            context["npdauser_list"] = queryset

            return render(
                request,
                "partials/npda_user_table.html",
                context=self.get_context_data(),
            )
        return response

    def post(self, request, *args: str, **kwargs) -> HttpResponse:
        """
        Override POST method to requery the database for the list of patients if  view preference changes
        """
        if request.htmx:
            view_preference = request.POST.get("view_preference", None)
            ods_code = request.POST.get("npdauser_ods_code_select_name", None)
            pz_code = request.POST.get("npdauser_pz_code_select_name", None)

            if ods_code:
                # call back from the organisation select
                # retrieve the sibling organisations and store in session
                sibling_organisations = retrieve_pdu_from_organisation_ods_code(
                    ods_code=ods_code
                )
                # store the results in session
                self.request.session["sibling_organisations"] = sibling_organisations
                self.request.session["ods_code"] = ods_code
            else:
                ods_code = request.session.get("sibling_organisations")[
                    "organisations"
                ][0][
                    "ods_code"
                ]  # set the ods code to the first in the list
                self.request.session["ods_code"] = ods_code

            if pz_code:
                # call back from the PDU select
                # retrieve the sibling organisations and store in session
                sibling_organisations = retrieve_pdu(pz_number=pz_code)
                # store the results in session
                self.request.session["sibling_organisations"] = sibling_organisations

                self.request.session["organisation_choices"] = [
                    (choice["ods_code"], choice["name"])
                    for choice in sibling_organisations["organisations"]
                ]
                ods_code = request.session.get("sibling_organisations")[
                    "organisations"
                ][0][
                    "ods_code"
                ]  # set the ods code to the first in the new list
                self.request.session["ods_code"] = ods_code
                self.request.session["pz_code"] = pz_code
            else:
                pz_code = request.session.get("sibling_organisations").get("pz_code")

            if view_preference:
                user = NPDAUser.objects.get(pk=request.user.pk)
                user.view_preference = view_preference
                user.save()
            else:
                user = NPDAUser.objects.get(pk=request.user.pk)

            context = {
                "view_preference": int(user.view_preference),
                "ods_code": ods_code,
                "pz_code": request.session.get("sibling_organisations").get("pz_code"),
                "hx_post": reverse_lazy("npda_users"),
                "organisation_choices": self.request.session.get(
                    "organisation_choices"
                ),
                "pdu_choices": self.request.session.get("pdu_choices"),
                "chosen_pdu": request.session.get("sibling_organisations").get(
                    "pz_code"
                ),
                "ods_code_select_name": "npdauser_ods_code_select_name",
                "pz_code_select_name": "npdauser_pz_code_select_name",
                "hx_target": "#npdauser_view_preference",
            }

            response = render(request, "partials/view_preference.html", context=context)

            trigger_client_event(
                response=response, name="npda_users", params={}
            )  # reloads the form to show the active steps
            return response

        return super().post(request, *args, **kwargs)


class NPDAUserCreateView(LoginAndOTPRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = NPDAUser
    form_class = NPDAUserForm

    def get_form_kwargs(self):
        # add the request object to the form kwargs
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

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

    def get_form_kwargs(self):
        # add the request object to the form kwargs
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit NPDA User Details"
        context["button_title"] = "Edit NPDA User Details"
        context["form_method"] = "update"
        context["npda_user"] = NPDAUser.objects.get(pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        organisation_employer = (
            form.cleaned_data["organisation_employer"][0]
            if form.cleaned_data["organisation_employer"]
            else None
        )
        if organisation_employer in instance.organisation_employer.all():
            # the employer has not changed
            instance.save()
        else:
            if organisation_employer:
                # the employer has changed
                instance.organisation_employer.clear()
                instance.organisation_employer.add(organisation_employer)
                instance.save()
            else:
                # there is no employer
                organisation = retrieve_pdu_from_organisation_ods_code(
                    self.request.session.get("ods_code")
                )
                # Get the name of the organistion from the API response
                matching_organisation = next(
                    (
                        org
                        for org in organisation["organisations"]
                        if org["ods_code"] == self.request.session.get("ods_code")
                    ),
                    None,
                )
                if matching_organisation:
                    # creat or update  the OrganisationEmployer object
                    new_employer, created = (
                        OrganisationEmployer.objects.update_or_create(
                            pz_code=self.request.session["pz_code"],
                            ods_code=self.request.session.get("ods_code"),
                            name=matching_organisation["name"],
                        )
                    )
                    # add the new employer to the user's employer list
                    instance.organisation_employer.add(new_employer)

        new_employer_ods_code = form.cleaned_data["add_employer"]
        if new_employer_ods_code:
            # a new employer has been added
            # fetch the organisation object from the API using the ODS code
            organisation = retrieve_pdu_from_organisation_ods_code(
                new_employer_ods_code
            )
            # Get the name of the organistion from the API response
            matching_organisation = next(
                (
                    org
                    for org in organisation["organisations"]
                    if org["ods_code"] == new_employer_ods_code
                ),
                None,
            )
            if matching_organisation:
                # creat or update  the OrganisationEmployer object
                new_employer, created = OrganisationEmployer.objects.update_or_create(
                    pz_code=organisation["pz_code"],
                    ods_code=new_employer_ods_code,
                    name=matching_organisation["name"],
                )
                # add the new employer to the user's employer list
                instance.organisation_employer.add(new_employer)

        instance.save()

        return super().form_valid(form)

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
                # successful login, get PDU and organisation details from user and store in session
                current_user_ods_code = (
                    self.request.user.organisation_employer.first().ods_code
                )
                current_user_pz_code = (
                    self.request.user.organisation_employer.first().pz_code
                )
                if "sibling_organisations" not in self.request.session:
                    # thisi s used to get all users in the same PDU in the PDUList view
                    sibling_organisations = retrieve_pdu_from_organisation_ods_code(
                        current_user_ods_code
                    )
                    # store the results in session
                    self.request.session["sibling_organisations"] = (
                        sibling_organisations
                    )

                # store the users PDU and ODS code in session as these are used to scope the data the user can see
                if "ods_code" not in self.request.session:
                    self.request.session["ods_code"] = current_user_ods_code

                if "pz_code" not in self.request.session:
                    self.request.session["pz_code"] = current_user_pz_code

                if "organisation_choices" not in self.request.session:
                    # get all NHS organisations in user's PDU as list of tuples (ODS code, name)
                    self.request.session["organisation_choices"] = [
                        (choice["ods_code"], choice["name"])
                        for choice in sibling_organisations["organisations"]
                    ]

                if "pdu_choices" not in self.request.session:
                    # this is a list of all pz_codes in the UK to populate the PDU selects
                    self.request.session["pdu_choices"] = retrieve_pdu_list()
                return redirect("home")

        # Otherwise, continue with usual workflow
        response = super().post(*args, **kwargs)
        return self.delete_cookies_from_response(response)

    # Override successful login redirect to org summary page
    def done(self, form_list, **kwargs):
        # this will not be called if debug=True
        response = super().done(form_list)
        response_url = getattr(response, "url")
        # successful login, get PDU, ODS and organisation details from user and store in session
        current_user_ods_code = self.request.user.organisation_employer.first().ods_code
        current_user_pz_code = self.request.user.organisation_employer.first().pz_code
        if "ods_code" not in self.request.session:
            self.request.session["ods_code"] = current_user_ods_code

        if "pz_code" not in self.request.session:
            self.request.session["pz_code"] = current_user_pz_code

        # if "sibling_organisations" not in self.request.session:
        #     sibling_organisations = retrieve_pdu_from_organisation_ods_code(
        #         current_user_ods_code
        #     )
        #     # store the results in session
        #     self.request.session["sibling_organisations"] = sibling_organisations

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
