from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand, CommandError
from httpx import AsyncClient, HTTPError

from project.constants.postcodes import (
    is_jersey_postcode,
    skip_api_validation_for_postcode,
)
from project.npda.general_functions.index_multiple_deprivation import imd_for_postcode
from project.npda.general_functions.validate_postcode import (
    country_from_validated_postcode,
    lookup_postcode,
    lookup_terminated_postcode,
)
from project.npda.models import AuditPeriod, Patient


def england_imd_year_for_audit_period(audit_period: AuditPeriod) -> int:
    """Map NPDA dataset year to England IMD publication year."""
    return 2025 if audit_period.get_dataset_year() >= 2026 else 2019


class Command(BaseCommand):
    help = (
        "Recalculate patient index_of_multiple_deprivation_quintile for one audit "
        "period using postcode country and audit-period-aware England year mapping."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--audit-period",
            type=str,
            help="Audit period slug (defaults to the current default audit period)",
        )
        parser.add_argument(
            "--pz-code",
            type=str,
            help="Optional PDU code filter",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Optional max number of patients to process",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Calculate but do not persist updates",
        )
        parser.add_argument(
            "--recalculate-missing",
            action="store_true",
            help=(
                "Only process patients with missing IMD quintile and a calculable "
                "non-Jersey postcode"
            ),
        )

    def _patients_queryset(self, audit_period, pz_code=None):
        queryset = Patient.objects.filter(
            submissions__submission_active=True,
            submissions__audit_period=audit_period,
        )

        if pz_code:
            queryset = queryset.filter(
                submissions__paediatric_diabetes_unit__pz_code=pz_code,
            )

        return queryset.distinct().order_by("pk")

    async def _recalculate_async(self, patient_rows, england_year):
        stats = {
            "processed": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
            "errors": 0,
        }
        updates = {}

        async with AsyncClient() as async_client:
            for patient in patient_rows:
                stats["processed"] += 1

                postcode = patient["postcode"]
                if (
                    not postcode
                    or skip_api_validation_for_postcode(postcode)
                    or is_jersey_postcode(postcode)
                ):
                    stats["skipped"] += 1
                    continue

                try:
                    validated = await lookup_postcode(postcode, async_client)
                    if not validated:
                        validated = await lookup_terminated_postcode(
                            postcode, async_client
                        )

                    if not validated:
                        stats["errors"] += 1
                        continue

                    country = country_from_validated_postcode(validated)
                    imd_year = england_year if country == "england" else None

                    imd_quintile = await imd_for_postcode(
                        validated.normalised_postcode,
                        async_client,
                        year=imd_year,
                        country=country,
                    )

                    if imd_quintile is None:
                        stats["errors"] += 1
                        continue

                    if (
                        patient["index_of_multiple_deprivation_quintile"]
                        == imd_quintile
                    ):
                        stats["unchanged"] += 1
                        continue

                    stats["updated"] += 1
                    updates[patient["id"]] = imd_quintile

                except HTTPError:
                    stats["errors"] += 1

        return stats, updates

    def handle(self, *args, **options):
        audit_period_slug = options.get("audit_period")
        pz_code = options.get("pz_code")
        limit = options.get("limit")
        dry_run = options.get("dry_run", False)
        recalculate_missing = options.get("recalculate_missing", False)

        if audit_period_slug:
            audit_period = AuditPeriod.objects.filter(slug=audit_period_slug).first()
            if not audit_period:
                raise CommandError(f"Unknown audit period slug: {audit_period_slug}")
        else:
            audit_period = AuditPeriod.objects.get_default_audit_period()

        england_year = england_imd_year_for_audit_period(audit_period)

        patients = self._patients_queryset(audit_period=audit_period, pz_code=pz_code)

        if limit:
            patients = patients[:limit]

        patient_rows = list(
            patients.values(
                "id",
                "postcode",
                "index_of_multiple_deprivation_quintile",
            )
        )

        if recalculate_missing:
            patient_rows = [
                patient
                for patient in patient_rows
                if patient["index_of_multiple_deprivation_quintile"] is None
                and patient["postcode"]
                and not skip_api_validation_for_postcode(patient["postcode"])
                and not is_jersey_postcode(patient["postcode"])
            ]

        total = len(patient_rows)
        self.stdout.write(
            self.style.NOTICE(
                "Recalculating IMD quintiles "
                f"for audit period '{audit_period.slug}' "
                f"(England year={england_year}) "
                f"across {total} patients"
                + (f" in {pz_code}" if pz_code else "")
                + (" [dry-run]" if dry_run else "")
                + (" [missing-only]" if recalculate_missing else "")
            )
        )

        stats, updates = async_to_sync(self._recalculate_async)(
            patient_rows, england_year
        )

        if not dry_run and updates:
            patients_to_update = list(Patient.objects.filter(id__in=updates.keys()))
            for patient in patients_to_update:
                patient.index_of_multiple_deprivation_quintile = updates[patient.id]

            Patient.objects.bulk_update(
                patients_to_update,
                ["index_of_multiple_deprivation_quintile"],
            )

        self.stdout.write("Finished.")
        self.stdout.write(f"Processed: {stats['processed']}")
        self.stdout.write(f"Updated: {stats['updated']}")
        self.stdout.write(f"Unchanged: {stats['unchanged']}")
        self.stdout.write(f"Skipped: {stats['skipped']}")
        self.stdout.write(f"Errors: {stats['errors']}")
