# 3rd Party Imports
from django_otp import DEVICE_ID_SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from django.urls import reverse
from two_factor.utils import default_device

# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
)


def twofactor_signin(client, test_user) -> None:
    """Helper fn to verify user via 2fa"""
    # OTP ENABLE
    test_user.totpdevice_set.create(name="default")
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = default_device(test_user).persistent_id
    session.save()


def set_session_attributes_for_user(client, user):
    """Helper fn to set session attributes for user, as done during login."""
    client.login(username=user.email, password="pw")

    request = RequestFactory().get(reverse("home"))
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session.save()

    sibling_organisations = get_single_pdu_from_ods_code("RP401")

    request.session["ods_code"] = user.organisation_employer
    request.session["sibling_organisations"] = sibling_organisations
    request.session["organisation_choices"] = [
        (choice["ods_code"], choice["name"])
        for choice in sibling_organisations["organisations"]
    ]
    request.session["pdu_choices"] = get_all_pdus_list_choices()
    request.session.save()

    client.cookies["sessionid"] = request.session.session_key

    # OTP
    twofactor_signin(client, user)
    return client
