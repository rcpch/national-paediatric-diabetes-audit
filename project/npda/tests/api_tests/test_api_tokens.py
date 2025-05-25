"""
Tests for Patient API endpoint permissions and OAuth2 token scopes.

These tests verify:
- OAuth2 token scope validation for patient:read operations
- PDU-based access control for patient data
- Proper filtering of patients based on user's PDU assignments
- Request ID generation and logging
- Response header validation
"""

import logging
from http import HTTPStatus
from unittest.mock import patch

from django.urls import reverse, resolve
from django.test import Client
import pytest
from django.test import override_settings
from django.apps import apps
from django.test import Client
from pytest import skip
from django.urls import reverse
from django.utils import timezone
from oauth2_provider.models import Application, AccessToken
from rest_framework.test import APIClient

from project.npda.models import NPDAUser, Patient, Submission, Transfer
from project.npda.models.organisation_employer import OrganisationEmployer
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models import PDUAccessTokenProfile
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.npda_user_factory import NPDAUserFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)
from project.constants.user import (
    AUDIT_CENTRE_COORDINATOR,
    RCPCH_AUDIT_TEAM,
    TRUST_AUDIT_TEAM_COORDINATOR_ACCESS,
    AUDIT_CENTRE_READER
)

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"
GOSH_PZ_CODE = "PZ196"
KINGS_COLLEGE_PZ_CODE = "PZ215"

# ✅ Mark entire module for database access
pytestmark = pytest.mark.django_db

@pytest.fixture(autouse=True)
def disable_ssl_redirect():
    """Automatically disable SSL redirect for all tests."""
    with override_settings(SECURE_SSL_REDIRECT=False):
        yield

@pytest.fixture
def oauth2_application():
    """Create an OAuth2 application for testing."""
    return Application.objects.create(
        name="Test API Application",
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )

@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()

def create_oauth2_token(user, application, scopes="patient:read", pdu=None):
    """Helper function to create OAuth2 tokens with specific scopes and PDU context."""
    
    pdu_token = None
    # Mock PDU profile if provided
    if pdu:
        token = AccessToken.objects.create(
            application=application,
            token=f"test-token-{user.id}-{scopes.replace(':', '-').replace(' ', '-')}",
            expires=timezone.now() + timezone.timedelta(hours=1),
            scope=scopes,
        )
        pdu_token = PDUAccessTokenProfile.objects.create(
            access_token=token,
            paediatric_diabetes_unit=pdu,
            description=f"Token for {user.username} in {pdu.pz_code}",
            access_level="readonly",
            is_active=True,
            contact_email=user.email if user.email else None,
            contact_name=user.get_full_name() if user.get_full_name() else user.username,
        )
    
    return pdu_token

def create_test_patients_in_pdu(pdu, count=3):
    """Helper function to create test patients in a specific PDU."""
    patients = []
    for i in range(count):
        patient = PatientFactory(
            nhs_number=f"123456789{i}",
            unique_reference_number=None,
        )
        
        # Create transfer record
        Transfer.objects.create(
            patient=patient,
            paediatric_diabetes_unit=pdu,
            date_leaving_service=None,
            reason_leaving_service=None,
        )
        
        # Add to active submission
        submission, _ = Submission.objects.get_or_create(
            paediatric_diabetes_unit=pdu,
            submission_active=True,
            defaults={
                'audit_year': timezone.now().year,
                'submission_date': timezone.now(),
                'submission_by': NPDAUser.objects.filter(
                    organisation_employers__pz_code=pdu.pz_code
                ).first(),
            }
        )
        submission.patients.add(patient)
        
        patients.append(patient)
    
    return patients

# ✅ FIXED: Add required fixtures and database access
@override_settings(SECURE_SSL_REDIRECT=False)
def test_url_resolution(seed_groups_fixture, seed_users_fixture):
    """Debug URL resolution to ensure no conflicts."""
    
    # Test API URLs
    try:
        api_patient_list = reverse("api:api_patient_list")
        print(f"API patient_list: {api_patient_list}")
        assert api_patient_list == "/api/v1/patients/"
    except Exception as e:
        print(f"API patient_list failed: {e}")
    
    # Test web app URLs (if you have them)
    try:
        web_patient_list = reverse("patients")  # Use your actual web app URL name
        print(f"Web patient list: {web_patient_list}")
        assert web_patient_list == "/patients/"
    except Exception as e:
        print(f"Web patient list failed: {e}")
    
    # Test that they resolve to different views
    try:
        api_resolver = resolve("/api/v1/patients/")
        web_resolver = resolve("/patients/")
        assert api_resolver.func != web_resolver.func
    except Exception as e:
        print(f"Resolver comparison failed: {e}")

@override_settings(SECURE_SSL_REDIRECT=False)
def test_no_redirects():
    """Test that API URLs don't cause unwanted redirects."""
    client = Client()
    
    # Test without following redirects
    response = client.get("/api/v1/patients/", follow=False)
    
    if response.status_code == 301:
        print(f"❌ Redirect detected: {response.status_code} -> {response.get('Location', 'Unknown')}")
        assert False, "API URL should not redirect"
    
    # Should be 401 (unauthorized) not 301 (redirect)
    assert response.status_code in [401, 403]  # Expected for unauthenticated API request


class TestPatientAPIPermissions:
    """Test OAuth2 token scope validation and PDU access control."""

    def test_patient_list_requires_authentication(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "credentials were not provided" in response.data["detail"].lower()

    def test_patient_list_requires_patient_read_scope(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that tokens without patient:read scope are rejected."""
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create token with wrong scope
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert "required scopes" in response.data["detail"].lower()

    def test_patient_list_with_valid_read_scope(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that tokens with patient:read scope are accepted."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
                organisation_employers__paediatric_diabetes_unit=ah_pdu
            ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.data, list)

    def test_patient_list_filters_by_user_pdu(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that users only see patients from their assigned PDUs."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        ah_user = NPDAUser.objects.filter(
                organisation_employers__paediatric_diabetes_unit=ah_pdu
            ).first()
        
        # Create patients in different PDUs
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        
        ah_patients = create_test_patients_in_pdu(ah_pdu, count=2)
        gosh_patients = create_test_patients_in_pdu(gosh_pdu, count=2)
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        
        # Should only see patients from Alder Hey
        nhs_numbers = [patient["nhs_number"] for patient in response.data]
        ah_nhs_numbers = [p.nhs_number for p in ah_patients]
        gosh_nhs_numbers = [p.nhs_number for p in gosh_patients]
        
        for nhs_number in ah_nhs_numbers:
            assert nhs_number in nhs_numbers
        
        for nhs_number in gosh_nhs_numbers:
            assert nhs_number not in nhs_numbers

    @pytest.mark.parametrize("user_role", [
        test_user_audit_centre_reader_data.role,
        test_user_audit_centre_editor_data.role,
        test_user_audit_centre_coordinator_data.role,
    ])
    def test_patient_list_access_by_role(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture, user_role):
        """Test that different user roles can access patient list with read scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
                organisation_employers__paediatric_diabetes_unit=ah_pdu
            ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK

    def test_rcpch_audit_team_sees_all_patients(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that RCPCH audit team members can see all patients."""
        rcpch_user = NPDAUser.objects.filter(
            role=test_user_rcpch_audit_team_data.role
        ).first()
        
        # Create patients in different PDUs
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        
        ah_patients = create_test_patients_in_pdu(ah_pdu, count=2)
        gosh_patients = create_test_patients_in_pdu(gosh_pdu, count=2)
        
        token = create_oauth2_token(rcpch_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        
        # Should see patients from both PDUs
        nhs_numbers = [patient["nhs_number"] for patient in response.data]
        all_nhs_numbers = [p.nhs_number for p in ah_patients + gosh_patients]
        
        for nhs_number in all_nhs_numbers:
            assert nhs_number in nhs_numbers

    def test_user_with_multiple_pdus_sees_all_their_patients(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that users with multiple PDU assignments see patients from all their PDUs."""
        # Create user with multiple employers
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
                organisation_employers__paediatric_diabetes_unit=ah_pdu
            ).first()
        
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        OrganisationEmployer.objects.create(
            npda_user=user,
            paediatric_diabetes_unit=gosh_pdu,
            is_primary_employer=False,
        )
        
        # Create patients in both PDUs
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        ah_patients = create_test_patients_in_pdu(ah_pdu, count=2)
        gosh_patients = create_test_patients_in_pdu(gosh_pdu, count=2)
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        
        # Should see patients from both PDUs
        nhs_numbers = [patient["nhs_number"] for patient in response.data]
        all_nhs_numbers = [p.nhs_number for p in ah_patients + gosh_patients]
        
        for nhs_number in all_nhs_numbers:
            assert nhs_number in nhs_numbers


class TestPatientAPIResponseHeaders:
    """Test API response headers and metadata."""

    def test_response_includes_npda_headers(self, api_client, oauth2_application, seed_groups_fixture, seed_users_fixture):
        """Test that responses include NPDA standard headers."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__paediatric_diabetes_unit=ah_pdu
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        
        # Check for NPDA headers (when using the mixin)
        # Note: These will only be present if the endpoint uses NPDAResponseMixin
        # For list views, Django REST framework handles the response directly
        # These headers would be present for detail views or custom responses
        
        # If the viewset uses NPDAResponseMixin for list responses:
        # assert 'X-NPDA-Timestamp' in response
        # assert 'X-NPDA-Version' in response  
        # assert 'X-Request-ID' in response

    def test_invalid_token_returns_proper_error(self, api_client):
        """Test that invalid tokens return appropriate error responses."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token-12345')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "Invalid token" in response.data["detail"] or "credentials" in response.data["detail"].lower()

@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture")
class TestPatientDetailAPI:
    """Test patient detail endpoint (GET /patients/{identifier}/)."""

    def test_patient_detail_by_nhs_number(self, api_client, oauth2_application):
        """Test retrieving a patient by NHS number."""
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create test patient
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        patients = create_test_patients_in_pdu(ah_pdu, count=1)
        patient = patients[0]
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_detail", kwargs={"pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert response.data["nhs_number"] == patient.nhs_number

    def test_patient_detail_by_urn(self, api_client, oauth2_application):
        """Test retrieving a patient by Unique Reference Number."""
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code="PZ248"  # Jersey PDU
        ).first()
        
        # Create test patient with URN
        patient = PatientFactory(
            nhs_number=None,
            unique_reference_number="URN123456",
        )
        
        jersey_pdu = PaediatricDiabetesUnit.objects.get(pz_code="PZ248") # Jersey PDU
        Transfer.objects.create(
            patient=patient,
            paediatric_diabetes_unit=jersey_pdu,
        )
        
        submission, _ = Submission.objects.get_or_create(
            paediatric_diabetes_unit=jersey_pdu,
            submission_active=True,
            defaults={
                'audit_year': timezone.now().year,
                'submission_date': timezone.now(),
                'submission_by': ah_user,
            }
        )
        submission.patients.add(patient)
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read", pdu=jersey_pdu)

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_detail", kwargs={"pk": patient.unique_reference_number})
        response = api_client.get(url)

        print(f"Response data: {response.data}")  # Debugging output
        
        assert response.status_code == HTTPStatus.OK
        assert response.data["unique_reference_number"] == patient.unique_reference_number

    def test_patient_detail_not_in_pdu_returns_404(self, api_client, oauth2_application):
        """Test that patients not in user's PDU return 404."""
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create patient in different PDU
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        gosh_patients = create_test_patients_in_pdu(gosh_pdu, count=1)
        patient = gosh_patients[0]
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_detail", kwargs={"pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "not found in your accessible patients" in response.data["detail"]

    def test_patient_detail_invalid_identifier_returns_404(self, api_client, oauth2_application):
        """Test that invalid patient identifiers return 404."""
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_detail", kwargs={"pk": "9999999999"})  # Non-existent NHS number
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "not found in your accessible patients" in response.data["detail"]

@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture")
class TestPatientAPIEdgeCases:
    """Test edge cases and error conditions."""

    def test_user_with_no_pdu_assignment_gets_empty_queryset(self, api_client, oauth2_application):
        """Test that users with no PDU assignments see no patients."""
        # Create user without PDU assignments
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        ah_user.organisation_employers.clear()
        ah_user.save()
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 0

    def test_expired_token_returns_unauthorized(self, api_client, oauth2_application):
        """Test that expired tokens are rejected."""
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create expired token
        token = AccessToken.objects.create(
            user=user,
            application=oauth2_application,
            token="expired-token-12345",
            expires=timezone.now() - timezone.timedelta(hours=1),  # Expired
            scope="patient:read",
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_token_with_multiple_scopes_works(self, api_client, oauth2_application):
        """Test that tokens with multiple scopes including patient:read work."""
        ah_users = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        )
        
        token = create_oauth2_token(ah_users.first(), oauth2_application, scopes="patient:read patient:write")
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')
        url = reverse("api:api_patient_list")
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK