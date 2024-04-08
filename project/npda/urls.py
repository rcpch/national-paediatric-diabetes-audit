from django.urls import path

from .views import *

urlpatterns = [
    path("home", view=home, name="home"),
    path("patients", view=patients, name="patients"),
    path("patients/<int:patient_id>", view=patient_visit, name="patient_visit"),
    path("<int:pk>/patient", view=PatientDetailView.as_view(), name="patientdetails"),
]
