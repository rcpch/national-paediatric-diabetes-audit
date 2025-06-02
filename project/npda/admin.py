from django.contrib import admin

# Import all models in the same order as they are declared in your models/__init__.py (if possible)
from .models import (
    AuditPeriod,
    NPDAUser,
    OrganisationEmployer,
    PaediatricDiabetesUnit,
    Patient,
    PDUAccessTokenProfile,
    Submission,
    Transfer,
    Visit,
    VisitActivity,
)

from django.contrib.sessions.models import Session


@admin.register(OrganisationEmployer)
class OrganisationEmployerAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "paediatric_diabetes_unit__pz_code",
        "paediatric_diabetes_unit__lead_organisation_ods_code",
        "paediatric_diabetes_unit__lead_organisation_name",
        "npda_user__email",
        "npda_user__first_name",
        "npda_user__surname",
    )
    list_display = (
        "pk",
        "paediatric_diabetes_unit__pz_code",
        "paediatric_diabetes_unit__lead_organisation_name",
        "npda_user__email",
        "npda_user__first_name",
        "npda_user__surname",
    )


@admin.register(NPDAUser)
class NPDAUserAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "email__icontains",
        "first_name__icontains",
        "surname__icontains",
    )
    list_display = ("email", "first_name", "surname", "role")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    search_fields = (
        "nhs_number__icontains",
        "pk",
        "unique_reference_number__icontains",
    )


@admin.register(PaediatricDiabetesUnit)
class PaediatricDiabetesUnitAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "pz_code",
        "lead_organisation_ods_code",
        "lead_organisation_name",
    )
    list_display = (
        "pz_code",
        "lead_organisation_ods_code",
        "lead_organisation_name",
        "active",
    )
    ordering = ("lead_organisation_name",)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    search_fields = ("paediatric_diabetes_unit", "patient", "pk")


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    search_fields = ("visit_date", "pk")


@admin.register(VisitActivity)
class VisitActivityAdmin(admin.ModelAdmin):
    search_fields = ("activity_datetime", "pk", "ip_address")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ["pk"]


@admin.register(AuditPeriod)
class AuditPeriodAdmin(admin.ModelAdmin):
    pass


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_key",
        "user_id",
        "pz_code",
        "organisation_choices",
        "pdu_choices",
        "expire_date",
    ]

    def session_data(self, obj):
        return obj.get_decoded()

    session_data.short_description = "Session Data"

    # Define the fields to be displayed in the admin panel
    def user_id(self, obj):
        return self.session_data(obj).get("_auth_user_id", "N/A")

    def pz_code(self, obj):
        return self.session_data(obj).get("pz_code", "N/A")

    def organisation_choices(self, obj):
        return self.session_data(obj).get("organisation_choices", "N/A")

    def pdu_choices(self, obj):
        return self.session_data(obj).get("pdu_choices", "N/A")

    user_id.short_description = "User ID"
    pz_code.short_description = "PZ Code"
    organisation_choices.short_description = "Organisation Choices"
    pdu_choices.short_description = "PDU Choices"

@admin.register(PDUAccessTokenProfile)
class PDUAccessTokenProfileAdmin(admin.ModelAdmin):
    search_fields = (
        "access_token__token",
        "paediatric_diabetes_unit__pz_code",
        "paediatric_diabetes_unit__parent_name",
        "description__icontains",
        "contact_email__icontains",
        "contact_name__icontains",
        "access_level__icontains",
        "is_active",
    )

admin.site.site_header = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.site_title = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.index_title = "RCPCH National Paediatric Diabetes Audit"
admin.site.site_url = "/"
