from django.conf import settings
from django.contrib import admin
from django.contrib.sessions.models import Session
from two_factor.admin import AdminSiteOTPRequiredMixin

from .models import (
    AuditPeriod,
    Banner,
    NPDAUser,
    OrganisationEmployer,
    PaediatricDiabetesUnit,
    Patient,
    Submission,
    Transfer,
    Visit,
    VisitActivity,
)


class NPDAAdminSite(AdminSiteOTPRequiredMixin, admin.AdminSite):
    def has_permission(self, request):
        if settings.LOCAL_DEV_BYPASS_2FA_AND_CAPTCHA and (
            request.user.is_superuser or request.user.is_staff
        ):
            return True

        return super().has_permission(request)


admin.site.__class__ = NPDAAdminSite


@admin.register(OrganisationEmployer)
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


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    search_fields = ("paediatric_diabetes_unit", "patient", "pk")


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    search_fields = ("visit_date", "pk")


@admin.register(VisitActivity)
class VisitActivityAdmin(admin.ModelAdmin):
    search_fields = ("activity_datetime", "pk", "ip_address")
    ordering = ("-activity_datetime",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    search_fields = ["pk"]


@admin.register(AuditPeriod)
class AuditPeriodAdmin(admin.ModelAdmin):
    pass


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    search_fields = ["pk"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_key",
        "user_id",
        "pz_code",
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

    user_id.short_description = "User ID"
    pz_code.short_description = "PZ Code"


admin.site.site_header = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.site_title = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.index_title = "RCPCH National Paediatric Diabetes Audit"
admin.site.site_url = "/"
