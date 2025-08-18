from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from oauth2_provider.models import Application, AccessToken
from oauth2_provider import settings as oauth2_settings
from django.utils import timezone
from datetime import timedelta
import secrets
from project.npda.models.access_tokens import PDUAccessTokenProfile
from project.npda.models import PaediatricDiabetesUnit

NPDAUser = get_user_model()

class Command(BaseCommand):
    help = 'Renew existing OAuth2 tokens with PDU scoping'
    
    def add_arguments(self, parser):
        parser.add_argument('--token', type=str, required=True, help='Current token to renew')
        parser.add_argument('--deactivate-old', action='store_true', default=True, help='Deactivate the old token (default: True)')
        parser.add_argument('--keep-old-active', action='store_true', help='Keep the old token active (overrides --deactivate-old)')
        parser.add_argument('--description', type=str, help='Update token description (optional)')
        parser.add_argument('--extend-expiry-days', type=int, help='Extend expiry by additional days beyond default')

    def handle(self, *args, **options):
        try:
            # Find the existing token
            try:
                old_access_token = AccessToken.objects.get(token=options['token'])
                self.stdout.write(f"✅ Found existing token (expires: {old_access_token.expires})")
            except AccessToken.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Token not found: {options['token'][:10]}..."))
                return

            # Get the PDU profile
            try:
                old_pdu_profile = PDUAccessTokenProfile.objects.get(access_token=old_access_token)
                self.stdout.write(f"✅ Found PDU profile for: {old_pdu_profile.paediatric_diabetes_unit.lead_organisation_name}")
            except PDUAccessTokenProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR("❌ No PDU profile found for this token"))
                return

            # Check if token is already expired
            if old_access_token.expires < timezone.now():
                self.stdout.write(self.style.WARNING(f"⚠️  Token expired {old_access_token.expires}, but proceeding with renewal"))

            # Generate new token
            new_token_string = secrets.token_urlsafe(32)
            
            # Calculate expiry (use custom extension if provided)
            base_expiry_seconds = oauth2_settings.oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS
            if options.get('extend_expiry_days'):
                additional_seconds = options['extend_expiry_days'] * 24 * 60 * 60
                expiry_seconds = base_expiry_seconds + additional_seconds
                self.stdout.write(f"🕒 Extended expiry by {options['extend_expiry_days']} days")
            else:
                expiry_seconds = base_expiry_seconds
            
            new_expires = timezone.now() + timedelta(seconds=expiry_seconds)

            # Create new access token with same properties as old one
            new_access_token = AccessToken.objects.create(
                user=old_access_token.user,
                application=old_access_token.application,
                token=new_token_string,
                expires=new_expires,
                scope=old_access_token.scope  # Inherit same scopes
            )

            # Create new PDU profile
            new_description = options.get('description', old_pdu_profile.description)
            if options.get('description'):
                new_description = f"{new_description} (renewed {timezone.now().strftime('%Y-%m-%d')})"
            
            new_pdu_profile = PDUAccessTokenProfile.objects.create(
                access_token=new_access_token,
                paediatric_diabetes_unit=old_pdu_profile.paediatric_diabetes_unit,
                description=new_description,
                access_level=old_pdu_profile.access_level,  # Inherit same access level
                contact_email=old_pdu_profile.contact_email,
                contact_name=old_pdu_profile.contact_name
            )

            # Handle old token deactivation
            should_deactivate = options.get('deactivate_old', True) and not options.get('keep_old_active', False)
            
            if should_deactivate:
                # Deactivate old PDU profile
                old_pdu_profile.is_active = False
                old_pdu_profile.save()
                
                # Set old token to expire immediately
                old_access_token.expires = timezone.now()
                old_access_token.save()
                
                self.stdout.write(f"🔒 Deactivated old token")
            else:
                self.stdout.write(f"⚠️  Old token remains active until {old_access_token.expires}")

            # Success output
            self.stdout.write(self.style.SUCCESS('\n🎉 Token renewed successfully!'))
            self.stdout.write(f"New Token: {new_token_string}")
            self.stdout.write(f"Expires: {new_expires}")
            self.stdout.write(f"Scopes: {new_access_token.scope}")
            self.stdout.write(f"PDU: {new_pdu_profile.paediatric_diabetes_unit.lead_organisation_name} ({new_pdu_profile.paediatric_diabetes_unit.pz_code})")
            self.stdout.write(f"Access Level: {new_pdu_profile.access_level}")
            self.stdout.write(f"User: {new_access_token.user.email}")
            
            self.stdout.write(self.style.WARNING('\n📋 For Postman:'))
            self.stdout.write(f"Authorization: Bearer {new_token_string}")

            # Show token status summary
            active_tokens = PDUAccessTokenProfile.objects.filter(
                paediatric_diabetes_unit=new_pdu_profile.paediatric_diabetes_unit,
                is_active=True
            ).count()
            self.stdout.write(f"\n📊 Total active tokens for this PDU: {active_tokens}")

            if not should_deactivate:
                self.stdout.write(self.style.WARNING(
                    "\n⚠️  Note: Both old and new tokens are currently active. "
                    "Remember to deactivate the old token when you're ready to switch."
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))