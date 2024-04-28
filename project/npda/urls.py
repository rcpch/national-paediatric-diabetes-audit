from django.urls import path, include
from django.contrib.auth.views import PasswordResetConfirmView, LoginView, LogoutView
from django.contrib.auth import urls as auth_urls
from project.npda.views import npda_users
from project.npda.views.visit import VisitCreateView, VisitDeleteView, VisitUpdateView, patient_visits
from project.npda.forms.npda_user_form import NPDAUpdatePasswordForm

from .views import *

urlpatterns = [
    path("captcha/", include("captcha.urls")),
    path("account/", include(auth_urls)),
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
    path(
        "npda_users",
        view=npda_users,
        name='npda_users'
    ),
    path(
        "npda_users/add",
        view=NPDAUserCreateView.as_view(),
        name='npdauser-create'
    ),
    path(
        "npda_users/<int:pk>/update",
        view=NPDAUserUpdateView.as_view(),
        name='npdauser-update'
    ),
    path(
        "npda_users/<int:pk>/delete",
        view=NPDAUserDeleteView.as_view(),
        name='npdauser-delete'
    ),
    path("captcha/", include("captcha.urls")),
    path("account/", include(auth_urls)),
    path(
        "account/password-reset/",
        view=ResetPasswordView.as_view(),
        name="password_reset",
    ),
    path(
        "account/password-reset-confirm/<uidb64>/<token>",
        view=PasswordResetConfirmView.as_view(
            form_class=NPDAUpdatePasswordForm,
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "account/login", view=LoginView.as_view(), name='login'
    ),
    path(
        "account/login", view=LogoutView.as_view(), name='logout'
    )
]
