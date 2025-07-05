from django.apps import apps
from django.contrib import admin

from .models import (
    NPDAUser,
    OrganisationEmployer,
    Patient,
    Visit,
    Transfer,
    VisitActivity,
    Submission,
    PaediatricDiabetesUnit,
    AuditPeriod
)
from django.contrib.sessions.models import Session


class NPDADjangoAdmin(admin.AdminSite):
    pass

admin_site = NPDADjangoAdmin(name="npda_admin")

class OrganisationEmployerAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "paediatric_diabetes_unit__pz_code",
        "paediatric_diabetes_unit__parent_ods_code",
        "paediatric_diabetes_unit__parent_name",
        "npda_user__email",
        "npda_user__first_name",
        "npda_user__surname",
    )
    list_display = (
        "pk",
        "paediatric_diabetes_unit__pz_code",
        "paediatric_diabetes_unit__parent_name",
        "npda_user__email",
        "npda_user__first_name",
        "npda_user__surname",
    )

class NPDAUserAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "email__icontains",
        "first_name__icontains",
        "surname__icontains",
    )
    list_display = ("email", "first_name", "surname", "role")


class PatientAdmin(admin.ModelAdmin):
    search_fields = (
        "nhs_number__icontains",
        "pk",
        "unique_reference_number__icontains",
    )


class PaediatricDiabetesUnitAdmin(admin.ModelAdmin):
    search_fields = (
        "pk",
        "pz_code",
        "parent_ods_code",
        "parent_name",
    )
    list_display = (
        "pz_code",
        "parent_ods_code",
        "parent_name",
        "active",
    )
    ordering = ("parent_name",)


class TransferAdmin(admin.ModelAdmin):
    search_fields = ("paediatric_diabetes_unit", "patient", "pk")


class VisitAdmin(admin.ModelAdmin):
    search_fields = ("visit_date", "pk")


class VisitActivityAdmin(admin.ModelAdmin):
    search_fields = ("activity_datetime", "pk", "ip_address")


class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ["pk"]


class AuditPeriodAdmin(admin.ModelAdmin):
    pass


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


admin_site.register(OrganisationEmployer, OrganisationEmployerAdmin)
admin_site.register(NPDAUser, NPDAUserAdmin)
admin_site.register(Patient, PatientAdmin)
admin_site.register(PaediatricDiabetesUnit, PaediatricDiabetesUnitAdmin)
admin_site.register(Transfer, TransferAdmin)
admin_site.register(Visit, VisitAdmin)
admin_site.register(VisitActivity, VisitActivityAdmin)
admin_site.register(Submission, SubmissionAdmin)
admin_site.register(AuditPeriod, AuditPeriodAdmin)
admin_site.register(Session, SessionAdmin)

admin_site.site_header = "RCPCH National Paediatric Diabetes Audit Admin"
admin_site.site_title = "RCPCH National Paediatric Diabetes Audit Admin"
admin_site.index_title = "RCPCH National Paediatric Diabetes Audit"
admin_site.site_url = "/"
