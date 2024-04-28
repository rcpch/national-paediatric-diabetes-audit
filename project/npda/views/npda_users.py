from datetime import datetime, timezone, timedelta
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.views import PasswordResetView, LoginView
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.utils.html import strip_tags
from django.conf import settings
from ..models import NPDAUser
from ..forms.npda_user_form import NPDAUserForm
from ..general_functions import (
    construct_confirm_email,
    send_email_to_recipients,
    construct_transfer_npda_site_email,
    construct_transfer_npda_site_outcome_email,
    group_for_role,
)


def npda_users(request):
    """
    Return a list of all children
    """
    template_name = "npda_users.html"
    npda_users = NPDAUser.objects.all()
    context = {"npda_users": npda_users}
    return render(request=request, template_name=template_name, context=context)


class NPDAUserCreateView(SuccessMessageMixin, CreateView):
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
        print("called")
        return reverse(
            "npda_users",
            # organisation_id=organisation_id,
        )


class NPDAUserUpdateView(SuccessMessageMixin, UpdateView):
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
        context["npda_user_id"] = self.kwargs["pk"]
        return context

    def is_valid(self):
        return super(NPDAUserForm, self).is_valid()


class NPDAUserDeleteView(SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = NPDAUser
    success_message = "NPDA User removed from database"
    success_url = reverse_lazy("npda_users")


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
    success_url = reverse_lazy("index")

    # extend form_valid to set user.password_last_set
    def form_valid(self, form):
        self.request.user.password_last_set = timezone.now()

        return super().form_valid(form)


# class RCPCHLoginView(LoginView):
