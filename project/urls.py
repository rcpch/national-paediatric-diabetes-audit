from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView
from two_factor.urls import urlpatterns as tf_urls
from .npda.views.npda_users import RCPCHLoginView


# from django.contrib.auth.views import LoginView
from .npda.viewsets import (
    UserViewSet,
    PatientViewSet,
    VisitViewSet,
)
from .npda.views import *

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"visits", VisitViewSet)
router.register(r"patients", PatientViewSet)

# OVERRIDE TWO_FACTOR LOGIN URL TO CAPTCHA LOGIN
for item in tf_urls:
    if type(item) == list:
        for url_pattern in item:
            if vars(url_pattern).get("name") == "login":
                url_pattern.callback = RCPCHLoginView.as_view()
        break

urlpatterns = [
    path("api/", include(router.urls)),
    path("admin/", admin.site.urls),
    path("", include(tf_urls)),
    path("api-auth/", include("rest_framework.urls")),
    # JSON Schema
    path("schema/", SpectacularJSONAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
    path("", include("project.npda.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
