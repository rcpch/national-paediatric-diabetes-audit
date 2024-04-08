from django.urls import path

from .views import *

urlpatterns = [
    path("home", view=home, name="home"),
    path("patients", view=patients, name="patients"),
    path("patients/<int:patient_id>", view=patient_visit, name="patient_visit"),
    path("patient/add/", PatientCreateView.as_view(), name="patient-add"),
    path("patient/<int:pk>/", PatientUpdateView.as_view(), name="patient-update"),
    path("patient/<int:pk>/delete/", PatientDeleteView.as_view(), name="patient-delete"),
]
