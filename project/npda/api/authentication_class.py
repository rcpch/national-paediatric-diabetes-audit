from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import exceptions
from project.npda.models.access_tokens import PDUAccessTokenProfile

class PDUScopedOAuth2Authentication(OAuth2Authentication):
    """
    OAuth2 authentication that also checks PDU scoping
    """
    
    def authenticate(self, request):
        # First, do the standard OAuth2 authentication
        result = super().authenticate(request)
        if not result:
            return None
            
        user, token = result
        
        # Check if this token has PDU scoping
        try:
            pdu_profile = PDUAccessTokenProfile.objects.get(access_token=token)
            if not pdu_profile.is_active:
                raise exceptions.AuthenticationFailed('Token has been revoked')
                
            # Add PDU context to the request for use in permissions
            request.pdu_profile = pdu_profile
            request.paediatric_diabetes_unit = pdu_profile.paediatric_diabetes_unit
            
        except PDUAccessTokenProfile.DoesNotExist:
            # Token exists but no PDU scoping - you can decide policy here
            request.pdu_profile = None
            request.paediatric_diabetes_unit = None
            
        return user, token