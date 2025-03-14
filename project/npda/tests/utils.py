# 3rd Party Imports
from datetime import date
from django_otp import DEVICE_ID_SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from two_factor.utils import default_device

from project.npda.models import NPDAUser, PaediatricDiabetesUnit, Submission
from project.npda.tests.UserDataClasses import test_user_audit_centre_reader_data
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from dateutil.relativedelta import relativedelta

# NPDA Imports


def twofactor_signin(client, test_user) -> None:
    """Helper fn to verify user via 2fa"""
    # OTP ENABLE
    test_user.totpdevice_set.create(name="default")
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = default_device(test_user).persistent_id
    session.save()


def login_and_verify_user(client, user):
    """Helper function to set session attributes for a signed-in user, as done during login."""
    # Log in the user
    client.login(username=user.email, password="pw")

    # # OTP Log in (assumed to be a custom function)
    twofactor_signin(client, user)

    return client


# Helper function for creating a submission
def create_submission(
    audit_start_date: date,
) -> Submission:
    """Default assumes patients are seeded at Alder Hey (ALDER_HEY_PZ_CODE fixture)

    We get the seeded Alder Hey user and use them to create a submission.
    """

    ah_user = NPDAUser.objects.get(
        first_name=test_user_audit_centre_reader_data.role_str,
        organisation_employers__pz_code=ALDER_HEY_PZ_CODE,
    )
    ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)

    return Submission.objects.create(
        paediatric_diabetes_unit=ah_pdu,
        audit_year=audit_start_date.year,
        submission_date=audit_start_date + relativedelta(days=1),
        submission_by=ah_user,
        submission_active=True,
    )
