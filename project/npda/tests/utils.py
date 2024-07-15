# 3rd Party Imports
from django_otp import DEVICE_ID_SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from two_factor.utils import default_device

# NPDA Imports
from project.npda.general_functions import (
    get_single_pdu_from_ods_code,
    get_all_pdus_list_choices,
    create_session_object_from_organisation_employer,
)
from project.npda.models.organisation_employer import OrganisationEmployer


def twofactor_signin(client, test_user) -> None:
    """Helper fn to verify user via 2fa"""
    # OTP ENABLE
    test_user.totpdevice_set.create(name="default")
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = default_device(test_user).persistent_id
    session.save()


def set_session_attributes_for_signedin_user(client, user):
    """Helper function to set session attributes for a signed-in user, as done during login."""
    # Log in the user
    client.login(username=user.email, password="pw")

    # Create a request to initiate the session
    request = RequestFactory().get("/")

    # Add the session middleware to process the request
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(request)
    request.session.save()

    # Update session data
    session_data = create_session_object_from_organisation_employer(
        user.organisation_employers.first()
    )
    request.session.update(session_data)
    request.session.save()

    # Update the client cookies to use the new session
    client.cookies["sessionid"] = request.session.session_key

    # OTP Log in (assumed to be a custom function)
    twofactor_signin(client, user)

    return client
