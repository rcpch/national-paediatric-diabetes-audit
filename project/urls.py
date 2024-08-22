"""
URL configuration for npda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from two_factor.urls import urlpatterns as tf_urls
from .npda.views.npda_users import RCPCHLoginView
from .npda.views import *

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
]
