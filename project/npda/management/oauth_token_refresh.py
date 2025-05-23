from django.core.management.base import BaseCommand
from oauth2_provider.models import Application
from project.npda.models import PaediatricDiabetesUnit

class Command(BaseCommand):
    help = 'Create an OAuth application that supports refresh tokens'

    def add_arguments(self, parser):
        parser.add_argument('--pz-code', type=str, required=True, help='PZ code of the PDU')
        parser.add_argument('--app-name', type=str, help='Custom application name')

    def handle(self, *args, **options):
        try:
            pdu = PaediatricDiabetesUnit.objects.get(pz_code=options['pz_code'])
            app_name = options.get('app_name') or f"PDU-{pdu.pz_code}-RefreshApp"
            
            # Create application with authorization code flow
            application = Application.objects.create(
                name=app_name,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,  # This supports refresh tokens
            )

            self.stdout.write(self.style.SUCCESS(f'🎉 Refresh-enabled OAuth Application created!'))
            self.stdout.write(f"Application Name: {application.name}")
            self.stdout.write(f"Client ID: {application.client_id}")
            self.stdout.write(f"Client Secret: {application.client_secret}")
            self.stdout.write(f"Authorization Grant Type: {application.authorization_grant_type}")
            
            self.stdout.write(self.style.WARNING('\n📋 Authorization URL:'))
            self.stdout.write(f"{{{{baseurl}}}}/api/o/authorize/?client_id={application.client_id}&response_type=code&scope=patient:read+patient:write")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))