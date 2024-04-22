# Django Imports
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def construct_confirm_email(request, user):
    """
    Generates email from template with hashed url to create password for user
    """

    email_template_name = "registration/admin_reset_password.html"
    c = {
        "email": user.email,
        'domain': get_current_site(request),
        'site_name': 'Epilepsy12',
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        'token': default_token_generator.make_token(user),
        'protocol': 'http',
    }
    email = render_to_string(email_template_name, c)

    return email



def send_email_to_recipients(recipients: list, subject: str, message: str):
    """
    Sends emails
    """
    send_mail(
        subject=subject,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
        message=strip_tags(message),
        html_message=message,
    )



def construct_transfer_npda_site_email(
    request, target_organisation, origin_organisation
):
    email_template_name = "registration/transfer_npda_site_email.html"
    c = {
        "domain": get_current_site(request),
        "site_name": "National Paediatric Diabetes Audit",
        "protocol": "http",
        "target_organisation": target_organisation,
        "origin_organisation": origin_organisation,
    }
    email = render_to_string(email_template_name, c)

    return email


def construct_transfer_npda_site_outcome_email(
    request, target_organisation, outcome
):
    email_template_name = "registration/transfer_npda_site_response.html"
    c = {
        "domain": get_current_site(request),
        "site_name": "National Paediatric Diabetes Audit",
        "protocol": "http",
        "target_organisation": target_organisation,
        "outcome": outcome,
    }
    email = render_to_string(email_template_name, c)

    return email
