"""
Tests for Visit API endpoint permissions and OAuth2 token scopes.

These tests verify:
- OAuth2 token scope validation for patient:read/write operations on visits
- PDU-based access control for visit data through patient scoping
- Proper filtering of visits based on user's PDU assignments
- Nested resource behavior (/patients/{id}/visits/)
- Visit creation, retrieval, and updates with proper validation
- Response structure and error handling
- Jersey PDU specific behavior using unique_reference_number
- Validation errors - errors bubbling up correctly for invalid requests
- Edge cases like non-existent patients/visits
"""

import logging
from http import HTTPStatus
from unittest.mock import patch
import json

from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
import pytest
from oauth2_provider.models import Application, AccessToken
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIClient

from project.npda.models import NPDAUser, Patient, Submission, Transfer, Visit
from project.npda.models.organisation_employer import OrganisationEmployer
from project.npda.models.paediatric_diabetes_unit import PaediatricDiabetesUnit
from project.npda.models import PDUAccessTokenProfile
from project.npda.tests.factories.patient_factory import PatientFactory
from project.npda.tests.factories.visit_factory import VisitFactory
from project.npda.tests.UserDataClasses import (
    test_user_audit_centre_coordinator_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_reader_data,
    test_user_rcpch_audit_team_data,
)

logger = logging.getLogger(__name__)

ALDER_HEY_PZ_CODE = "PZ074"
GOSH_PZ_CODE = "PZ196"
KINGS_COLLEGE_PZ_CODE = "PZ215"
JERSEY_PZ_CODE = "PZ248"

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
        name="Test Visit API Application",
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
    )

@pytest.fixture
def api_client():
    """Create an API client for testing."""
    client = APIClient()
    return client

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
            access_level="readonly" if "read" in scopes else "readwrite",
            is_active=True,
            contact_email=user.email if user.email else None,
            contact_name=user.get_full_name() if user.get_full_name() else user.username,
        )
    
    print(pdu_token)
    print(scopes)
    
    return pdu_token

def create_test_patient_with_visits(pdu, visit_count=3):
    """Helper function to create a test patient with visits in a specific PDU."""
    patient = PatientFactory(
        nhs_number=f"987654321{pdu.pk}",
        unique_reference_number=None,
        diagnosis_date="2024-01-01",
    )
    
    # Create transfer record
    Transfer.objects.create(
        patient=patient,
        paediatric_diabetes_unit=pdu,
        date_leaving_service=None,
        reason_leaving_service=None,
    )
    
    # Add to active submission
    user = NPDAUser.objects.filter(
        organisation_employers__pz_code=pdu.pz_code
    ).first()
    
    submission, _ = Submission.objects.get_or_create(
        paediatric_diabetes_unit=pdu,
        submission_active=True,
        defaults={
            'audit_year': timezone.now().year,
            'submission_date': timezone.now(),
            'submission_by': user,
        }
    )
    submission.patients.add(patient)
    
    # Create visits for this patient
    visits = []
    for i in range(visit_count):
        visit = VisitFactory(
            patient=patient,
            visit_date=timezone.now().date() - timezone.timedelta(days=i*30),
            height=150.0 + i,
            weight=45.0 + i,
        )
        visits.append(visit)
    
    return patient, visits

@override_settings(SECURE_SSL_REDIRECT=False)
def test_visit_url_resolution(seed_groups_fixture, seed_users_fixture, seed_audit_periods_fixture):
    """Test that visit URLs resolve correctly."""
    # Test nested visit URLs
    visit_list_url = reverse("api:api_patient_visits", kwargs={"patient_pk": "1234567890"})
    assert visit_list_url == "/api/v1/patients/1234567890/visits/"
    
    visit_detail_url = reverse("api:api_patient_visit_detail", kwargs={"patient_pk": "1234567890", "pk": 123})
    assert visit_detail_url == "/api/v1/patients/1234567890/visits/123/"


@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture")
class TestVisitAPIPermissions:
    """Test OAuth2 token scope validation and PDU access control for visits."""

    def test_visit_list_requires_authentication(self, api_client):
        """Test that unauthenticated requests are rejected."""
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": "1234567890"})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert "credentials were not provided" in response.data["detail"].lower()

    def test_visit_list_requires_patient_read_scope(self, api_client, oauth2_application):
        """Test that tokens without patient:read scope are rejected."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create token with wrong scope
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=2)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert "you do not have permission to perform this action." in response.data["detail"].lower()

    def test_visit_list_with_valid_read_scope(self, api_client, oauth2_application):
        """Test that tokens with patient:read scope can list visits."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=3)
        # the patient factory creates a patient with a visit without a date so we need to remove it
        Visit.objects.filter(patient=patient, visit_date__isnull=True).delete()
        assert Visit.objects.all().count() == 3
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.data, list)
        assert len(response.data) == 3
        
        # Check that visit data is returned (not patient info)
        visit_data = response.data[0]
        assert "id" in visit_data
        assert "visit_date" in visit_data
        assert "height" in visit_data
        assert "weight" in visit_data
        # Patient context should NOT be in the response (clean nested resource)
        assert "patient_identifier" not in visit_data
        assert "patient_info" not in visit_data

    def test_visit_list_filters_by_patient_pdu_access(self, api_client, oauth2_application):
        """Test that users can only see visits for patients in their PDU."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create patients and visits in different PDUs
        ah_patient, ah_visits = create_test_patient_with_visits(ah_pdu, visit_count=2)
        gosh_patient, gosh_visits = create_test_patient_with_visits(gosh_pdu, visit_count=2)
        # the patient factory creates a patient with a visit without a date so we need to remove it
        Visit.objects.filter(visit_date__isnull=True).delete()
        assert Visit.objects.all().count() == 4
        
        # Create token for Alder Hey user
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        # Should be able to access Alder Hey patient visits
        ah_url = reverse("api:api_patient_visits", kwargs={"patient_pk": ah_patient.nhs_number})
        ah_response = api_client.get(ah_url)
        assert ah_response.status_code == HTTPStatus.OK
        assert len(ah_response.data) == 2
        
        # Should NOT be able to access GOSH patient visits
        gosh_url = reverse("api:api_patient_visits", kwargs={"patient_pk": gosh_patient.nhs_number})
        gosh_response = api_client.get(gosh_url)
        assert gosh_response.status_code == HTTPStatus.NOT_FOUND
        assert "Patient not accessible within your PDU scope" in gosh_response.data["detail"]

    def test_visit_detail_requires_patient_read_scope(self, api_client, oauth2_application):
        """Test that visit detail endpoint requires proper scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=1)
        visit = visits[0]
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient.nhs_number,
            "pk": visit.id
        })
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert response.data["id"] == visit.id
        assert response.data["visit_date"] == visit.visit_date.isoformat()

    def test_visit_detail_wrong_patient_returns_404(self, api_client, oauth2_application):
        """Test that accessing a visit with wrong patient ID returns 404."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient1, visits1 = create_test_patient_with_visits(ah_pdu, visit_count=1)
        patient2, visits2 = create_test_patient_with_visits(ah_pdu, visit_count=1)
        
        # Try to access patient1's visit through patient2's URL
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient2.nhs_number,  # Wrong patient
            "pk": visits1[0].id  # Patient1's visit
        })
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_jersey_pdu_uses_urn_for_patient_lookup(self, api_client, oauth2_application):
        """Test that Jersey PDU (PZ248) uses unique_reference_number for patient lookup."""
        jersey_pdu = PaediatricDiabetesUnit.objects.get(pz_code=JERSEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=JERSEY_PZ_CODE
        ).first()
        
        # Create patient with URN (no NHS number)
        patient = PatientFactory(
            nhs_number=None,
            unique_reference_number="URN123456",
        )
        #  Patient factory creates a patient with a visit without a date so we need to remove it
        Visit.objects.filter(patient=patient).delete()  # Ensure no visits
        
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
                'submission_by': user,
            }
        )
        submission.patients.add(patient)
        
        # Create a visit
        visit = VisitFactory(patient=patient)
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=jersey_pdu)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.unique_reference_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 1


@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture")
class TestVisitAPIWriteOperations:
    """Test visit creation and update operations."""

    def test_visit_create_requires_patient_write_scope(self, api_client, oauth2_application):
        """Test that creating visits requires patient:write scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create token with only read scope
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=0)
        
        visit_data = {
            "visit_date": "2024-01-15",
            "height": 155.5,
            "weight": 50.2,
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.post(url, data=visit_data, format='json')
        
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_visit_create_with_write_scope(self, api_client, oauth2_application):
        """Test that creating visits works with patient:write scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=0)
        
        visit_data = {
            "visit_date": "2024-01-15", # date after the patient's diagnosis date
            "height": 155.5,
            "weight": 50.2,
            "height_weight_observation_date": "2024-01-15",
            "hba1c": 65,
            "hba1c_format": 1,  # mmol/mol
            "hba1c_date": "2024-01-15",
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.post(url, data=visit_data, format='json')
        
        assert response.status_code == HTTPStatus.CREATED
        assert response.data["visit_date"] == "2024-01-15"
        assert response.data["height"] == "155.5"
        assert response.data["weight"] == "50.2"
        assert "bmi" in response.data  # Should be calculated
        
        # Verify visit was created in database
        created_visit = Visit.objects.get(id=response.data["id"])
        assert created_visit.patient == patient

    def test_visit_create_for_patient_not_in_pdu_fails(self, api_client, oauth2_application):
        """Test that creating visits for patients outside PDU scope fails."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        
        ah_user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(ah_user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        # Create patient in different PDU
        gosh_patient, _ = create_test_patient_with_visits(gosh_pdu, visit_count=0)
        
        visit_data = {
            "visit_date": "2024-01-15",
            "height": 155.5,
            "weight": 50.2,
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": gosh_patient.nhs_number})
        response = api_client.post(url, data=visit_data, format='json')
        
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_visit_create_with_invalid_data_returns_validation_errors(self, api_client, oauth2_application):
        """Test that invalid visit data returns proper validation errors."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=0)
        
        # Invalid data - missing required visit_date
        invalid_visit_data = {
            "height": 155.5,
            "weight": 50.2,
            # Missing visit_date which is required
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.post(url, data=invalid_visit_data, format='json')
        
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "visit_date" in response.data

    def test_visit_update_requires_patient_write_scope(self, api_client, oauth2_application):
        """Test that updating visits requires patient:write scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create token with only read scope
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=1)
        visit = visits[0]
        
        update_data = {
            "height": 160.0,
            "weight": 55.0,
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient.nhs_number,
            "pk": visit.id
        })
        response = api_client.patch(url, data=update_data, format='json')
        
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_visit_update_with_write_scope(self, api_client, oauth2_application):
        """Test that updating visits works with patient:write scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=1)
        visit = visits[0]
        original_height = visit.height
        
        update_data = {
            "height": 160.0,
            "weight": 55.0,
            "height_weight_observation_date": "2024-01-15",
            "visit_date": "2024-01-15",  # Ensure date is after diagnosis
        }
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient.nhs_number,
            "pk": visit.id
        })
        response = api_client.patch(url, data=update_data, format='json')
        
        assert response.status_code == HTTPStatus.OK
        assert response.data["height"] == "160.0"
        assert response.data["weight"] == "55.0"
        
        # Verify visit was updated in database
        updated_visit = Visit.objects.get(id=visit.id)
        assert updated_visit.height != original_height
        assert float(updated_visit.height) == 160.0

    def test_visit_delete_not_allowed(self, api_client, oauth2_application):
        """Test that DELETE operations are not allowed on visits."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:write", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=1)
        visit = visits[0]
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient.nhs_number,
            "pk": visit.id
        })
        response = api_client.delete(url)
        
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
        assert 'Method "DELETE" not allowed.' in response.data["detail"]


@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture")
class TestVisitAPIEdgeCases:
    """Test edge cases and error conditions for visit API."""

    def test_visit_list_for_nonexistent_patient(self, api_client, oauth2_application):
        """Test that requesting visits for non-existent patient returns 404."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": "9999999999"})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "Patient with identifier '9999999999' not found" in response.data["detail"]

    def test_visit_detail_for_nonexistent_visit(self, api_client, oauth2_application):
        """Test that requesting non-existent visit returns 404."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=0)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visit_detail", kwargs={
            "patient_pk": patient.nhs_number,
            "pk": 99999
        })
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "Visit with ID '99999' not found" in response.data["detail"]

    def test_visit_list_empty_for_patient_with_no_visits(self, api_client, oauth2_application):
        """Test that patients with no visits return empty list."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=0)
        Visit.objects.filter(patient=patient).delete()  # Ensure no visits exist
        assert Visit.objects.all().count() == 0
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_token_with_multiple_scopes_including_patient_read_works(self, api_client, oauth2_application):
        """Test that tokens with multiple scopes including patient:read work."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read patient:write admin", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=2)
        Visit.objects.filter(visit_date__isnull=True).delete()  # Ensure no visits without date
        assert Visit.objects.all().count() == 2
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 2

    def test_expired_token_returns_unauthorized_for_visits(self, api_client, oauth2_application):
        """Test that expired tokens are rejected for visit endpoints."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        # Create expired token
        token = AccessToken.objects.create(
            application=oauth2_application,
            expires=timezone.now() - timezone.timedelta(hours=1),  # Expired
            scope="patient:read",
        )

        pdu_token = PDUAccessTokenProfile.objects.create(
            access_token=token,
            paediatric_diabetes_unit=ah_pdu,
            description=f"Expired token for {user.username}",
            access_level="readonly",
            is_active=True,
            contact_email=user.email,
            contact_name=user.get_full_name(),
        )
        
        patient, _ = create_test_patient_with_visits(ah_pdu, visit_count=1)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {pdu_token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures("seed_groups_fixture", "seed_users_fixture", "seed_audit_periods_fixture") 
class TestVisitAPIUserRoles:
    """Test visit API access for different user roles."""

    @pytest.mark.parametrize("user_role", [
        test_user_audit_centre_reader_data.role,
        test_user_audit_centre_editor_data.role,
        test_user_audit_centre_coordinator_data.role,
    ])
    def test_visit_list_access_by_role(self, api_client, oauth2_application, user_role):
        """Test that different user roles can access visit lists with read scope."""
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        user = NPDAUser.objects.filter(
            organisation_employers__pz_code=ALDER_HEY_PZ_CODE
        ).first()
        
        token = create_oauth2_token(user, oauth2_application, scopes="patient:read", pdu=ah_pdu)
        
        patient, visits = create_test_patient_with_visits(ah_pdu, visit_count=2)
        # the patient factory creates a patient with a visit without a date so we need to remove it
        Visit.objects.filter(visit_date__isnull=True).delete()
        assert Visit.objects.all().count() == 2
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        url = reverse("api:api_patient_visits", kwargs={"patient_pk": patient.nhs_number})
        response = api_client.get(url)
        
        assert response.status_code == HTTPStatus.OK
        assert len(response.data) == 2

    def test_rcpch_audit_team_sees_visits_across_pdus(self, api_client, oauth2_application):
        """Test that RCPCH audit team members can see visits from any PDU."""
        rcpch_user = NPDAUser.objects.filter(
            role=test_user_rcpch_audit_team_data.role
        ).first()
        
        ah_pdu = PaediatricDiabetesUnit.objects.get(pz_code=ALDER_HEY_PZ_CODE)
        gosh_pdu = PaediatricDiabetesUnit.objects.get(pz_code=GOSH_PZ_CODE)
        
        # Create patients and visits in different PDUs
        ah_patient, ah_visits = create_test_patient_with_visits(ah_pdu, visit_count=2)
        gosh_patient, gosh_visits = create_test_patient_with_visits(gosh_pdu, visit_count=2)
        # the patient factory creates a patient with a visit without a date so we need to remove it
        Visit.objects.filter(visit_date__isnull=True).delete()
        assert Visit.objects.all().count() == 4
        # RCPCH user should have access to both PDUs
        
        # Use any PDU for token (RCPCH should see all)
        token = create_oauth2_token(rcpch_user, oauth2_application, scopes="admin", pdu=ah_pdu)
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        # Should be able to access both PDU patients' visits
        ah_url = reverse("api:api_patient_visits", kwargs={"patient_pk": ah_patient.nhs_number})
        ah_response = api_client.get(ah_url)
        assert ah_response.status_code == HTTPStatus.OK
        assert len(ah_response.data) == 2
        
        gosh_url = reverse("api:api_patient_visits", kwargs={"patient_pk": gosh_patient.nhs_number})
        gosh_response = api_client.get(gosh_url)
        assert gosh_response.status_code == HTTPStatus.OK
        assert len(gosh_response.data) == 2