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
    help = 'Create a PDU-scoped API token for testing'

    from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create OAuth2 tokens with PDU scoping'
    
    def get_scopes_for_access_level(self, access_level):
        """
        Map access levels to appropriate OAuth scopes.
        Patient scopes cover both patient and visit data.
        """
        scope_mappings = {
            'readonly': [
                'patient:read'
            ],
            'readwrite': [
                'patient:read', 
                'patient:write'
            ],
            'admin': [
                'patient:read', 
                'patient:write',
                'admin:cross-pdu'  # Special scope for cross-PDU access
            ]
        }
        return ' '.join(scope_mappings.get(access_level, ['patient:read']))

    def add_arguments(self, parser):
        parser.add_argument('--user-email', type=str, required=True, help='Email of the user')
        parser.add_argument('--pz-code', type=str, required=True, help='PZ code of the PDU')
        parser.add_argument('--application-name', type=str, help='Name of the OAuth application')
        parser.add_argument('--create-application', action='store_true', help='Auto-create OAuth application for this PDU')
        parser.add_argument('--description', type=str, default='API testing token', help='Token description')
        parser.add_argument('--access-level', type=str, default='readonly', choices=['readonly', 'readwrite', 'admin'], help='Access level')
        parser.add_argument('--scopes', type=str, default='patient:read', help='Token scopes (space-separated)')

    def handle(self, *args, **options):
        try:
            # Get the user
            npda_user = NPDAUser.objects.get(email=options['user_email'])
            self.stdout.write(f"✅ Found user: {npda_user.email}")

            # Get the PDU
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=options['pz_code'])
            self.stdout.write(f"✅ Found PDU: {pdu.lead_organisation_name} ({pdu.pz_code})")

            # Determine scopes: use provided scopes or auto-determine from access level
            if options.get('scopes'):
                token_scopes = options['scopes']
                self.stdout.write(f"📝 Using provided scopes: {token_scopes}")
            else:
                token_scopes = self.get_scopes_for_access_level(options['access_level'])
                self.stdout.write(f"🔧 Auto-determined scopes for '{options['access_level']}': {token_scopes}")

            # Get or create the application
            if options.get('create_application'):
                # Auto-create application - application-name is optional
                application_name = f"PDU-{pdu.pz_code}-API"
                application, created = Application.objects.get_or_create(
                    name=application_name,
                    defaults={
                        'client_type': Application.CLIENT_CONFIDENTIAL,
                        'authorization_grant_type': Application.GRANT_CLIENT_CREDENTIALS,
                    }
                )
                if created:
                    self.stdout.write(f"✅ Created new application: {application.name}")
                    self.stdout.write(f"   Client ID: {application.client_id}")
                    self.stdout.write(f"   Client Secret: {application.client_secret}")
                    self.stdout.write(self.style.WARNING("   ⚠️  Save these credentials securely!"))
                else:
                    self.stdout.write(f"✅ Using existing application: {application.name}")
            else:
                # Use existing application - application-name is required
                if not options.get('application_name'):
                    self.stdout.write(
                        self.style.ERROR(
                            "❌ Error: When not using --create-application, you must provide --application-name\n"
                            "   Either use --create-application to auto-create, or specify --application-name"
                        )
                    )
                    return
                
                try:
                    application = Application.objects.get(name=options['application_name'])
                    self.stdout.write(f"✅ Found application: {application.name}")
                except Application.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Application '{options['application_name']}' not found\n"
                            "   Available applications:"
                        )
                    )
                    # Show available applications to help the user
                    available_apps = Application.objects.all()[:5]
                    for app in available_apps:
                        self.stdout.write(f"     - {app.name}")
                    if Application.objects.count() > 5:
                        self.stdout.write(f"     ... and {Application.objects.count() - 5} more")
                    return

            # Generate a secure token
            token_string = secrets.token_urlsafe(32)

            # Create the access token
            expires = timezone.now() + timedelta(seconds=oauth2_settings.oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
            
            access_token = AccessToken.objects.create(
                user=npda_user,
                application=application,
                token=token_string,
                expires=expires,
                scope=token_scopes  # Use the determined scopes
            )

            # Create the PDU profile
            pdu_profile = PDUAccessTokenProfile.objects.create(
                access_token=access_token,
                paediatric_diabetes_unit=pdu,
                description=options['description'],
                access_level=options['access_level'],
                contact_email=npda_user.email,
                contact_name=npda_user.get_full_name() or npda_user.username
            )

            self.stdout.write(self.style.SUCCESS('\n🎉 Token created successfully!'))
            self.stdout.write(f"Token: {token_string}")
            self.stdout.write(f"Expires: {expires}")
            self.stdout.write(f"Scopes: {token_scopes}")
            self.stdout.write(f"PDU: {pdu.lead_organisation_name} ({pdu.pz_code})")
            self.stdout.write(f"Access Level: {options['access_level']}")
            self.stdout.write(f"Application: {application.name}")
            
            self.stdout.write(self.style.WARNING('\n📋 For Postman:'))
            self.stdout.write(f"Authorization: Bearer {token_string}")

            # Show existing tokens for this PDU
            existing_tokens = PDUAccessTokenProfile.objects.filter(
                paediatric_diabetes_unit=pdu,
                is_active=True
            ).count()
            self.stdout.write(f"\n📊 Total active tokens for this PDU: {existing_tokens}")

            # Show scope mapping for reference
            self.stdout.write(self.style.WARNING('\n📚 Available access levels and their scopes:'))
            for level in ['readonly', 'readwrite', 'admin']:
                scopes = self.get_scopes_for_access_level(level)
                self.stdout.write(f"   {level}: {scopes}")

        except NPDAUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User with email '{options['user_email']}' not found"))
        except PaediatricDiabetesUnit.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ PDU with code '{options['pz_code']}' not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))