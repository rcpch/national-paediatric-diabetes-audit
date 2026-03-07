# 3rd Party Imports
from datetime import date
from django_otp import DEVICE_ID_SESSION_KEY
from django.contrib.sessions.middleware import SessionMiddleware
from django.test.client import RequestFactory
from two_factor.utils import default_device

from project.npda.models import AuditPeriod, PaediatricDiabetesUnit, Submission
from project.npda.tests.UserDataClasses import test_user_audit_centre_reader_data
from project.npda.tests.constants_for_tests import ALDER_HEY_PZ_CODE
from dateutil.relativedelta import relativedelta

from project.npda.tests.factories.npda_user_factory import NPDAUserFactory

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
    audit_start_date_or_audit_period: date | AuditPeriod,
    pz_code: str,
    csv_file_name: str | None = None,
    csv_file: bytes | None = None,
) -> Submission:
    """

    We use the provided pz_code to seed auser and use them to create a submission.
    """

    if isinstance(audit_start_date_or_audit_period, AuditPeriod):
        audit_period = audit_start_date_or_audit_period
        audit_start_date = audit_period.start_date
    else:
        audit_start_date = audit_start_date_or_audit_period
        audit_period = AuditPeriod.objects.get(start_date=audit_start_date)

    npda_user = NPDAUserFactory(
        first_name="test",
        role=test_user_audit_centre_reader_data.role,
        # Assign flags based on user role
        is_active=test_user_audit_centre_reader_data.is_active,
        is_staff=test_user_audit_centre_reader_data.is_staff,
        is_rcpch_audit_team_member=test_user_audit_centre_reader_data.is_rcpch_audit_team_member,
        is_rcpch_staff=test_user_audit_centre_reader_data.is_rcpch_staff,
        groups=[test_user_audit_centre_reader_data.group_name],
        # Assign to PDU via organisation employer by passing in list of pz_codes
        organisation_employers=[pz_code],
    )
    pdu = PaediatricDiabetesUnit.objects.get(pz_code=pz_code)

    # Ensure a single active submission per PDU/year for tests that hit update_or_create.
    Submission.objects.filter(
        paediatric_diabetes_unit=pdu,
        audit_year=audit_start_date.year,
        submission_active=True,
    ).update(submission_active=False)

    return Submission.objects.create(
        paediatric_diabetes_unit=pdu,
        audit_year=audit_start_date.year,
        audit_period=audit_period,
        submission_date=audit_start_date + relativedelta(days=1),
        submission_by=npda_user,
        submission_active=True,
        csv_file_name=csv_file_name,
        csv_file=csv_file,
    )
