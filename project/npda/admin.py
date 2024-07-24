from django.contrib import admin

from .models import NPDAUser, OrganisationEmployer, Patient, Site, Visit, VisitActivity, AuditCohort
from django.contrib.sessions.models import Session


@admin.register(OrganisationEmployer)
class OrganisationEmployerAdmin(admin.ModelAdmin):
    search_fields = ("name", "pk", "ods_code", "pz_code")


@admin.register(NPDAUser)
class NPDAUserAdmin(admin.ModelAdmin):
    search_fields = ("surname_icontains", "pk")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    search_fields = ("nhs_number_icontains", "pk")


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    search_fields = ("organisation", "pk")


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    search_fields = ("visit_date", "pk")


@admin.register(VisitActivity)
class VisitActivityAdmin(admin.ModelAdmin):
    search_fields = ("activity_datetime", "pk", "ip_address")

@admin.register(AuditCohort)
class AuditCohortAdmin(admin.ModelAdmin):
    search_fields = ["pk"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    
    list_display = ['session_key', 'user_id', 'ods_code', 'pz_code', 'organisation_choices', 'pdu_choices', 'expire_date']

    def session_data(self, obj):
        return obj.get_decoded()

    session_data.short_description = 'Session Data'
    
    # Define the fields to be displayed in the admin panel
    def user_id(self, obj):
        return self.session_data(obj).get('_auth_user_id', 'N/A')

    def ods_code(self, obj):
        return self.session_data(obj).get('ods_code', 'N/A')

    def pz_code(self, obj):
        return self.session_data(obj).get('pz_code', 'N/A')

    def organisation_choices(self, obj):
        return self.session_data(obj).get('organisation_choices', 'N/A')

    def pdu_choices(self, obj):
        return self.session_data(obj).get('pdu_choices', 'N/A')

    user_id.short_description = 'User ID'
    ods_code.short_description = 'ODS Code'
    pz_code.short_description = 'PZ Code'
    organisation_choices.short_description = 'Organisation Choices'
    pdu_choices.short_description = 'PDU Choices'


admin.site.site_header = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.site_title = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.index_title = "RCPCH National Paediatric Diabetes Audit"
admin.site.site_url = "/"
