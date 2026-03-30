from django.core.management.base import BaseCommand
from django.db.models import BooleanField, Case, Q, When
from django.forms import ValidationError

from project.npda.forms.external_patient_validators import validate_patient_sync
from project.npda.forms.external_visit_validators import validate_visit_sync
from project.npda.models import Patient, Visit

# Recalculates external fields for existing patients and visits.
# For use after the APIs are restored post downtime.


def find_affected_patients_and_visits():
    patients = Patient.objects.all().annotate(
        missing_location=Case(
            When(
                Q(location_bng__isnull=True) | Q(location_wgs84__isnull=True), then=True
            ),
            output_field=BooleanField(),
        ),
        missing_gp_practice=Case(
            When(
                Q(gp_practice_ods_code__isnull=True)
                | Q(gp_practice_postcode__isnull=True),
                then=True,
            ),
            output_field=BooleanField(),
        ),
        missing_imd=Case(
            When(Q(index_of_multiple_deprivation_quintile__isnull=True), then=True),
            output_field=BooleanField(),
        ),
    )

    visits = Visit.objects.all().annotate(
        missing_height_data=Case(
            When(
                Q(height__isnull=False)
                & (Q(height_centile__isnull=True) | Q(height_sds__isnull=True)),
                then=True,
            ),
            output_field=BooleanField(),
        ),
        missing_weight_data=Case(
            When(
                Q(weight__isnull=False)
                & (Q(weight_centile__isnull=True) | Q(weight_sds__isnull=True)),
                then=True,
            ),
            output_field=BooleanField(),
        ),
        missing_bmi_data=Case(
            When(
                Q(bmi__isnull=False)
                & (Q(bmi_centile__isnull=True) | Q(bmi_sds__isnull=True)),
                then=True,
            ),
            output_field=BooleanField(),
        ),
    )

    print("Summary to fix:")
    print(
        f"  Patients missing location: {patients.filter(missing_location__gt=0).count()}"
    )
    print(
        f"  Patients missing GP practice details: {patients.filter(missing_gp_practice__gt=0).count()}"
    )
    print(
        f"  Patients missing IMD quintile: {patients.filter(missing_imd__gt=0).count()}"
    )
    print(
        f"  Visits missing height centiles/z-scores: {visits.filter(missing_height_data__gt=0).count()}"
    )
    print(
        f"  Visits missing weight centiles/z-scores: {visits.filter(missing_weight_data__gt=0).count()}"
    )
    print(
        f"  Visits missing BMI centiles/z-scores: {visits.filter(missing_bmi_data__gt=0).count()}"
    )
    print("")
    print(
        "NOTE: the above will include patients/visits which cannot be fixed due to missing data (eg postcode, sex etc)"
    )
    print(
        "This command will attempt to fix those but will be unable to. This is expected."
    )

    patients = patients.filter(
        Q(missing_location=True) | Q(missing_gp_practice=True) | Q(missing_imd=True)
    )

    visits = visits.filter(
        Q(missing_height_data=True)
        | Q(missing_weight_data=True)
        | Q(missing_bmi_data=True)
    )

    return (patients, visits)


class Command(BaseCommand):
    help = "Recalculates missing external fields for existing patients and visits."

    def update_external_patient_field(self, field_name, obj, result):
        old_value = getattr(obj, field_name)
        new_value = getattr(result, field_name)

        if old_value is None and (
            new_value is not None and not isinstance(new_value, ValidationError)
        ):
            setattr(obj, field_name, new_value)
            obj.save()

            print(f"\t{field_name}", end="", flush=True)

    def update_external_visit_fields(self, field_name, obj, result):
        requires_updating = (
            getattr(obj, f"{field_name}_centile") is None
            or getattr(obj, f"{field_name}_sds") is None
        )

        can_update = getattr(
            result, f"{field_name}_result"
        ) is not None and not isinstance(
            getattr(result, f"{field_name}_result"), ValidationError
        )

        if requires_updating and can_update:
            centile_sds = getattr(result, f"{field_name}_result")

            setattr(obj, f"{field_name}_centile", centile_sds.centile)
            setattr(obj, f"{field_name}_sds", centile_sds.sds)
            obj.save()

            print(f"\t{field_name}_centile\t{field_name}_sds", end="", flush=True)

            if field_name == "bmi":
                obj.bmi = result.bmi
                obj.save()

                print("\t bmi", end="", flush=True)

    def handle(self, *args, **options):
        patients, visits = find_affected_patients_and_visits()

        choice = input("Do you want to proceed? Y/n").lower()
        if choice != "y":
            print("Aborting.")
            return

        for patient in patients:
            identifier = patient.unique_reference_number or patient.nhs_number
            print(f"[{identifier}]", end="", flush=True)

            result = validate_patient_sync(
                postcode=patient.postcode,
                gp_practice_ods_code=patient.gp_practice_ods_code,
                gp_practice_postcode=patient.gp_practice_postcode,
            )

            for field_name in [
                "gp_practice_ods_code",
                "gp_practice_postcode",
                "location_bng",
                "location_wgs84",
                "index_of_multiple_deprivation_quintile",
            ]:
                self.update_external_patient_field(field_name, patient, result)

            print("")

        for visit in visits:
            identifier = (
                visit.patient.unique_reference_number or visit.patient.nhs_number
            )
            date = (
                visit.visit_date.strftime("%Y-%m-%d")
                if visit.visit_date
                else "unknown date"
            )
            print(f"[{identifier} - {date}]", end="", flush=True)

            result = validate_visit_sync(
                birth_date=visit.patient.date_of_birth,
                observation_date=visit.visit_date,
                sex=visit.patient.sex,
                height=visit.height,
                weight=visit.weight,
            )

            for field_name in ["height", "weight", "bmi"]:
                self.update_external_visit_fields(field_name, visit, result)

            print("")
