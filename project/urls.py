# Django imports
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# Third-party imports
from two_factor.urls import urlpatterns as tf_urls
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Local imports
from .npda.views.npda_users import RCPCHLoginView
from .npda.views import *

# Custom error pages
handler400 = "project.npda.views.error_400"
handler403 = "project.npda.views.error_403"
handler404 = "project.npda.views.error_404"
handler500 = "project.npda.views.error_500"

# OVERRIDE TWO_FACTOR LOGIN URL TO CAPTCHA LOGIN
for item in tf_urls:
    if type(item) == list:
        for url_pattern in item:
            if vars(url_pattern).get("name") == "login":
                url_pattern.callback = RCPCHLoginView.as_view()
        break

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(tf_urls)),
    path("", include("project.npda.urls")),
    path("api/v1/", include("project.npda.api.urls", namespace="api")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    # path(
    #     "api/v1/schema/swagger-ui/",
    #     SpectacularSwaggerView.as_view(url_name="schema"),
    #     name="swagger-ui",
    # ),
    path("api/v1/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="redoc"),
    # path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)