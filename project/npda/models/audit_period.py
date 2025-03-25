from django.contrib.gis.db import models
from django.core.exceptions import ValidationError


class AuditPeriodManager(models.Manager):
    def get_default_audit_period(self):
        audit_period = self.get_queryset().filter(is_open=True).earliest("start_date")

        if not audit_period:
            audit_period = self.get_queryset().first()

            if not audit_period:
                raise ValidationError("No audit periods. Restart or run `python manage.py seed --mode=seed_audit_periods` manually")

        return audit_period

    def get_audit_period_for_request(self, request):
        # TODO MRB: cache all this
        # TODO MRB: make backwards compatible with old sessions (audit year based rather than period)
        selected_audit_period_id = request.session.get("selected_audit_period_id", None)

        if selected_audit_period_id:
            return AuditPeriod.objects.get(pk=selected_audit_period_id)


class AuditPeriod(models.Model):
    objects = AuditPeriodManager()

    is_open = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField()

    def display_name(self):
        return f"{self.start_date.year} - {self.end_date.year}"

    def is_allowed_to_edit(self, user):
        return (user and (user.is_superuser or user.is_rcpch_audit_team_member)) or self.is_open

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("Audit start date must be before the audit end date.")

    def __str__(self):
        return f"AuditPeriod {self.start_date} - {self.end_date}"