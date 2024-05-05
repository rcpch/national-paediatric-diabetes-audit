from django.contrib import admin

from .models import Patient, Visit, NPDAUser, VisitActivity

# Register your models here.
admin.site.register(NPDAUser)
admin.site.register(Patient)
admin.site.register(Visit)
admin.site.register(VisitActivity)
