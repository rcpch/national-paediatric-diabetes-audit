from datetime import date

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

    # TODO MRB: replace with the check_data_permissions mixin?
    def get_audit_period_for_request(self, request):
        selected_audit_year = request.session.get("selected_audit_year", None)

        audit_period = AuditPeriod.objects.filter(
            start_date__year=selected_audit_year
        ).first()
        
        return audit_period


class AuditPeriod(models.Model):
    objects = AuditPeriodManager()

    is_open = models.BooleanField()
    is_visible = models.BooleanField()

    start_date = models.DateField()
    end_date = models.DateField()

    slug = models.SlugField(unique=True)

    # For compatibility with old code
    def audit_year(self):
        return self.start_date.year

    def display_name(self):
        return f"{self.start_date.year} - {self.end_date.year}"

    def is_allowed_to_edit(self, user):
        return (user and (user.is_superuser or user.is_rcpch_audit_team_member)) or self.is_open
    
    def kpi_calculation_date(self):
        today = date.today()
    
        if self.start_date > today:
            # Future audit period - likely no data yet but you can still select it
            return self.start_date
        elif today > self.end_date:
            # Past audit period
            return self.end_date
        else:
            # Current audit period
            return today

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("Audit start date must be before the audit end date.")

    def __str__(self):
        return f"AuditPeriod {self.start_date} - {self.end_date}"