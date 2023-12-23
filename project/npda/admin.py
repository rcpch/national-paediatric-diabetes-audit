from django.contrib import admin

from .models import Patient, Visit, PaediatricDiabetesUnit, Organisation, NPDAUser

# Register your models here.
admin.site.register(Patient)
admin.site.register(Visit)
admin.site.register(PaediatricDiabetesUnit)
admin.site.register(Organisation)
admin.site.register(NPDAUser)
