from django.contrib import admin

from .models import NPDAUser, OrganisationEmployer, Patient, Site, Visit, VisitActivity


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


@admin.register(OrganisationEmployer)
class OrganisationEmployerAdmin(admin.ModelAdmin):
    search_fields = ("name", "pk", "ods_code", "pz_code")


admin.site.site_header = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.site_title = "RCPCH National Paediatric Diabetes Audit Admin"
admin.site.index_title = "RCPCH National Paediatric Diabetes Audit"
admin.site.site_url = "/"
