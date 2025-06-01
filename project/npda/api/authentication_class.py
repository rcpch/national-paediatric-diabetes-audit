import pytz
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import exceptions
from django.utils import timezone
from drf_spectacular.authentication import OpenApiAuthenticationExtension
from project.npda.models import PDUAccessTokenProfile
import logging
from project.npda.models.access_tokens import AccessToken

logger = logging.getLogger(__name__)


class PDUScopedOAuth2Authentication(OAuth2Authentication):
    """
    OAuth2 authentication that also checks PDU scoping and handles token expiry
    """
    
    def authenticate(self, request):
        # First, do the standard OAuth2 authentication
        result = super().authenticate(request)
        if not result:
            return None
            
        user, token = result

        # Get current time in UTC
        now = timezone.now()

       # Log what we received from the database
        token_expires = token.expires

        logger.debug(f"Received token: {token.token}, expires at: {token_expires}, current time: {now}")

        if now > token_expires:
            raise exceptions.AuthenticationFailed('Token has expired')
        
        # Use raw times for expiry warning too
        time_until_expiry = token_expires - now
        if time_until_expiry.total_seconds() < 300:  # 5 minutes
            request.META['HTTP_TOKEN_EXPIRES_SOON'] = 'true'
            request.META['HTTP_TOKEN_EXPIRES_IN'] = str(int(time_until_expiry.total_seconds()))
        
        # Check if this token has PDU scoping
        try:
            pdu_profile = PDUAccessTokenProfile.objects.get(access_token=token)
            if not pdu_profile.is_active:
                raise exceptions.AuthenticationFailed('Token has been revoked')
                
            # Add PDU context to the request (for backward compatibility)
            request.pdu_profile = pdu_profile
            request.paediatric_diabetes_unit = pdu_profile.paediatric_diabetes_unit
            
            # ✅ KEY FIX: Also attach to the token object for permission class access
            token.pdu_profile = pdu_profile
            
            logger.debug(f"✅ PDU profile attached: {pdu_profile.access_level} for PDU {pdu_profile.paediatric_diabetes_unit.pz_code}")
            
        except PDUAccessTokenProfile.DoesNotExist:
            # Token exists but no PDU scoping
            request.pdu_profile = None
            request.paediatric_diabetes_unit = None
            token.pdu_profile = None
            logger.warning(f"❌ No PDU profile found for token {token.token}")
            
        return user, token

class PDUAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'project.npda.api.authentication_class.PDUScopedOAuth2Authentication'
    name = 'PDUScopedOAuth2Authentication'
    match_subclasses = False

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer'
        }

    def get_security_requirement(self, auto_schema):
        return {'PDUScopedOAuth2Authentication': []}
    def get_authentication(self, auto_schema):
        return PDUScopedOAuth2Authentication()
    def get_operation_security(self, auto_schema, operation):
        # Ensure that the operation has the correct security requirements
        if 'PDUScopedOAuth2Authentication' not in operation.security:
            operation.security.append({'PDUScopedOAuth2Authentication': []})
        return operation.security
    def get_operation_parameters(self, auto_schema, operation):
        # Add any additional parameters if needed
        return operation.parameters
    def get_operation_responses(self, auto_schema, operation):
        # Ensure that the operation has the correct responses
        if '401' not in operation.responses:
            operation.responses['401'] = {
                'description': 'Unauthorized',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {
                                    'type': 'string',
                                    'example': 'Authentication credentials were not provided.'
                                }
                            }
                        }
                    }
                }
            }
        return operation.responses
    def get_operation_tags(self, auto_schema, operation):
        # Ensure that the operation has the correct tags
        if 'PDUScopedOAuth2Authentication' not in operation.tags:
            operation.tags.append('PDUScopedOAuth2Authentication')
        return operation.tags
    def get_operation_summary(self, auto_schema, operation):
        # Ensure that the operation has a summary
        if not operation.summary:
            operation.summary = 'PDU Scoped OAuth2 Authentication'
        return operation.summary
    def get_operation_description(self, auto_schema, operation):
        # Ensure that the operation has a description
        if not operation.description:
            operation.description = 'This operation uses PDU Scoped OAuth2 Authentication.'
        return operation.description
    def get_operation_deprecated(self, auto_schema, operation):
        # Ensure that the operation is not deprecated
        if operation.deprecated is None:
            operation.deprecated = False
        return operation.deprecated
    def get_operation_external_docs(self, auto_schema, operation):
        # Ensure that the operation has external documentation if needed
        if not operation.external_docs:
            operation.external_docs = {
                'description': 'Find out more about PDU Scoped OAuth2 Authentication',
                'url': 'https://example.com/pdu-scoped-oauth2-authentication'
            }
        return operation.external_docs