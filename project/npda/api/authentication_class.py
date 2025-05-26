from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import exceptions
from django.utils import timezone
from project.npda.models import PDUAccessTokenProfile
import logging

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
        
        # Check if token is expired
        if token.expires < timezone.now():
            raise exceptions.AuthenticationFailed('Token has expired')
        
        # Check if token is close to expiry (within 5 minutes)
        time_until_expiry = token.expires - timezone.now()
        if time_until_expiry.total_seconds() < 300:  # 5 minutes
            # Add a header to warn about upcoming expiry
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