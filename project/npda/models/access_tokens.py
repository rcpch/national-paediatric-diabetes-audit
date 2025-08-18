from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
from oauth2_provider.models import AccessToken

class PDUAccessTokenProfile(models.Model):
    """
    Additional profile data for OAuth access tokens scoped to PDUs
    """
    # Link to the standard OAuth access token
    access_token = models.OneToOneField(
        AccessToken,
        on_delete=models.CASCADE,
        related_name='pdu_profile'
    )
    
    # Your custom PDU scoping
    paediatric_diabetes_unit = models.ForeignKey(
        'npda.PaediatricDiabetesUnit',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='pdu_access_token_profiles'
    )
    
    # All your custom fields
    description = models.CharField(max_length=255, blank=True, null=True)
    access_level = models.CharField(max_length=20, default='readonly')
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        app_label = "npda"
        verbose_name = "PDU Access Token Profile"
        verbose_name_plural = "PDU Access Token Profiles"

    @property
    def pz_code(self):
        return self.paediatric_diabetes_unit.pz_code if self.paediatric_diabetes_unit else None
    
    def revoke(self, reason='other', details=None):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save()
        # Also revoke the underlying OAuth token
        self.access_token.delete()