from django.urls import path

from .views import *

urlpatterns = [
    path("home", view=home, name="home"),
    path("patients", view=patients, name="patients"),
    path("patient/<int:patient_id>/visits", view=patient_visits, name="patient_visits"),
    path(
        "patient/<int:patient_id>/visits/create",
        view=VisitCreateView.as_view(),
        name="visit-create",
    ),
    path(
        "patient/<int:patient_id>/visits/<int:pk>/update",
        view=VisitUpdateView.as_view(),
        name="visit-update",
    ),
    path(
        "patient/<int:patient_id>/visits/<int:pk>/delete",
        view=VisitDeleteView.as_view(),
        name="visit-delete",
    ),
    path("patient/add/", PatientCreateView.as_view(), name="patient-add"),
    path(
        "patient/<int:pk>/update",
        PatientUpdateView.as_view(),
        name="patient-update",
    ),
    path(
        "patient/<int:pk>/delete",
        PatientDeleteView.as_view(),
        name="patient-delete",
    ),
]
