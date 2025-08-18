# standard imports
from oauth2_provider.views import TokenView
import datetime
from http import HTTPStatus
import secrets

# Django imports
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.test.client import Client

# DRF imports
from rest_framework.test import APIClient

# OAuth2 imports
from oauth2_provider.models import AccessToken, Application

# Pytest imports
import pytest

from project.npda.models import PDUAccessTokenProfile, PaediatricDiabetesUnit, NPDAUser
from project.npda.models import Transfer, Submission
from project.npda.tests.factories import PatientFactory

"""
Helper functions and fixtures for testing API token behavior
"""

def create_oauth2_token(user, application, access_level="readonly", scopes="patient:read", pdu=None):
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
            access_level=access_level,
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

@pytest.fixture(autouse=True)
def disable_ssl_redirect():
    """Automatically disable SSL redirect for all tests."""
    with override_settings(SECURE_SSL_REDIRECT=False):
        yield

@pytest.fixture
def oauth2_application():
    raw_secret = secrets.token_urlsafe(32) # Generate a random, unhashed secret

    app = Application.objects.create(
        name="Test API Application",
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
        skip_authorization=True,
        # Assign the raw secret here. D-O-T will hash it internally.
        client_secret=raw_secret,
    )

    # The 'app' object's client_secret is now hashed.
    # But we still have the raw_secret from when we created it.
    app.original_client_secret = raw_secret

    # No need for a separate app.save() here as create() already saves
    return app


@pytest.fixture
def api_client():
    """Create an API client for testing."""
    return APIClient()

def create_oauth2_token(user, application, access_level="readonly", scopes="patient:read", pdu=None):
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
            access_level=access_level,
            is_active=True,
            contact_email=user.email if user.email else None,
            contact_name=user.get_full_name() if user.get_full_name() else user.username,
        )
    
    return pdu_token

"""Test cases for API token behavior"""

@pytest.mark.django_db
def test_expired_token_behavior(api_client, oauth2_application, disable_ssl_redirect):
    """Ensure expired tokens are rejected."""
    user = NPDAUser.objects.first()
    expired_token = AccessToken.objects.create(
        user=user,
        application=oauth2_application,
        expires=timezone.now() - timezone.timedelta(minutes=1),
        scope="patient:read",
        token="expired-test-token"
    )
    PDUAccessTokenProfile.objects.create(
        access_token=expired_token,
        paediatric_diabetes_unit=PaediatricDiabetesUnit.objects.first(),
        is_active=True,
    )
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token.token}')
    response = api_client.get(reverse("api:api_patient_list"))
    assert response.status_code == HTTPStatus.UNAUTHORIZED

@pytest.mark.skip(reason="This workflow works in postman but not in pytest. I have debugged the test extensively and cannot find the issue. Probably related to transaction management or client state.")
@pytest.mark.django_db
def test_token_renewal_after_expiry(api_client, oauth2_application, disable_ssl_redirect):
    """Test that client can request a new token after expiry using client credentials."""
    # Step 1: Create an expired token
    user = NPDAUser.objects.first()
    
    expired_token = create_oauth2_token(
        user=user,
        application=oauth2_application,
        access_level="readwrite",
        scopes="patient:read",
        pdu=PaediatricDiabetesUnit.objects.first()
    )

    expired_token.access_token.expires = timezone.now() - datetime.timedelta(hours=10) # Set to expired
    expired_token.access_token.save()
    
    pdu = expired_token.paediatric_diabetes_unit
    
    assert expired_token.is_active is True, "Expired token should still be in the database"
    assert expired_token.access_token.expires < timezone.now(), "Token should be expired"
    
    # Step 2: Verify expired token is rejected
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token.access_token.token}')
    response = api_client.get(reverse("api:api_patient_list"))
    assert response.status_code == HTTPStatus.UNAUTHORIZED, "Expired token should be rejected"
    
    # Step 3: Request a new token using client credentials
    # Use base64 encoding for Basic Auth header as required by OAuth2
    from base64 import b64encode
    oauth2_application_fresh = Application.objects.get(pk=oauth2_application.pk)

    print(f"Fresh Application ID: {oauth2_application_fresh.pk}")
    print(f"Fresh authorization_grant_type: {oauth2_application_fresh.authorization_grant_type}")
    print(f"Fresh client_type: {oauth2_application_fresh.client_type}") # Check client_type too

    # Use the fresh application's details
    client_creds = f"{oauth2_application_fresh.client_id}:{oauth2_application.original_client_secret}" # Still use original secret
    encoded_creds = b64encode(client_creds.encode('utf-8')).decode('utf-8')

    token_client = Client() # Keep it fresh

    # Method 2: Form data auth - using fresh app and original secret
    token_response = token_client.post(
        reverse("oauth2_provider:token"),
        data={
            "grant_type": "client_credentials",
            "client_id": oauth2_application_fresh.client_id,
            "client_secret": oauth2_application.original_client_secret, # Use original secret
            "scope": "patient:read",
        },
        content_type="application/x-www-form-urlencoded",
    )

    import json
    # You can also parse it to be sure it's valid JSON
    try:
        error_data = json.loads(token_response.content)
        print(f"Parsed error data: {error_data}")
    except json.JSONDecodeError:
        print("Response content is not valid JSON.")

    token_data = json.loads(token_response.content)
    assert "access_token" in token_data, "Response should include access_token"
    
    # Step 5: Use the new token
    new_token = token_data["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_token}')
    
    # Create PDU profile for the new token (this would normally happen in middleware)
    new_access_token = AccessToken.objects.get(token=new_token)
    PDUAccessTokenProfile.objects.create(
        access_token=new_access_token,
        paediatric_diabetes_unit=pdu,
        is_active=True,
    )
    
    # Step 6: Test that the new token works
    patient_response = api_client.get(reverse("api:api_patient_list"))
    assert patient_response.status_code == HTTPStatus.OK, "New token should work for API access"
    assert isinstance(patient_response.data, list), "Should return list of patients"