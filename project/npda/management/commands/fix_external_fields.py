from django.core.management.base import BaseCommand
from django.db.models import Q

from project.npda.models import Patient, Visit

# Recalculates external fields for existing patients and visits.
# For use after the APIs are restored post downtime.

def fix_external_fields():
    missing_location_count = Patient.objects.filter(
        Q(location_bng__isnull=True) |
        Q(location_wgs84__isnull=True)
    ).count()
    
    missing_gp_practice_count = Patient.objects.filter(
        Q(gp_practice_ods_code__isnull=True) |
        Q(gp_practice_postcode__isnull=True)
    ).count()

    missing_imd_count = Patient.objects.filter(
        index_of_multiple_deprivation_quintile__isnull=True
    ).count()

    missing_centiles_count = Visit.objects.filter(
        Q(height_centile__isnull=True) |
        Q(height_sds__isnull=True) |
        Q(weight_centile__isnull=True) |
        Q(weight_sds__isnull=True) |
        Q(height_centile__isnull=True) |
        Q(bmi__isnull=True) |
        Q(bmi_centile__isnull=True) |
        Q(bmi_sds__isnull=True)
    ).count()

    print(f"Summary to fix:")
    print(f"  Patients missing location: {missing_location_count}")
    print(f"  Patients missing GP practice details: {missing_gp_practice_count}")
    print(f"  Patients missing IMD quintile: {missing_imd_count}")
    print(f"  Visits missing centiles/z-scores: {missing_centiles_count}")
    print(f"")
    print(f"NOTE: the above will include patients/visits which cannot be fixed due to missing data (eg postcode, sex etc)")
    print(f"This command will attempt to fix those but will be unable to. This is expected.")


class Command(BaseCommand):
    help = "Recalculates missing external fields for existing patients and visits."

    def handle(self, *args, **options):
        fix_external_fields()
        

