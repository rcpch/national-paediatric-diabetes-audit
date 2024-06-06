"""
Django settings for npda project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
import logging

#  django imports
from django.core.management.utils import get_random_secret_key

# RCPCH imports
from .logging_settings import (
    LOGGING,
)  # no it is not an unused import, it pulls LOGGING into the settings file

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") + [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
]
CSRF_TRUSTED_ORIGINS = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") + [
    "https://127.0.0.1",
    "https://localhost",
    "https://0.0.0.0",
]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())

# This is the token required for getting deprivation quintiles from the RCPCH Census Platform
RCPCH_CENSUS_PLATFORM_URL = os.getenv("RCPCH_CENSUS_PLATFORM_URL")
RCPCH_CENSUS_PLATFORM_TOKEN = os.getenv("RCPCH_CENSUS_PLATFORM_TOKEN")
# TODO #83  - Fix the broken env in Azure and remove hardcoded URL
RCPCH_NHS_ORGANISATIONS_API_URL = os.getenv("RCPCH_NHS_ORGANISATIONS_API_URL")
RCPCH_NHS_ORGANISATIONS_API_URL = "https://rcpch-nhs-organisations.azurewebsites.net"

# This is the NHS Spine services - it does not require authentication
# It is possible to retrieve the ods code from the NHS API above, but not to narrow down
# by organisation type - many practices host multiple entities (pharmacies, private companies etc)
# and it is not possible to filter out just the Prescribing Cost Centres, which is NHS digital
# jargon for a GP practice
NHS_SPINE_SERVICES_URL = os.getenv("NHS_SPINE_SERVICES_URL")

POSTCODE_API_BASE_URL = os.getenv("POSTCODE_API_BASE_URL")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"
if DEBUG is True:
    CAPTCHA_TEST_MODE = True  # if in debug mode, can just type 'PASSED' and captcha validates. Default value is False

# GENERAL CAPTCHA SETTINGS
CAPTCHA_IMAGE_SIZE = (200, 50)
CAPTCHA_FONT_SIZE = 40

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # "django.forms",
    "rest_framework",
    "drf_spectacular",
    # django htmx
    "django_htmx",
    # 2fa
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",
    "two_factor.plugins.email",
    "two_factor",
    "two_factor.plugins.phonenumber",  # we don't use phones currently but required for app to work
    "captcha",
    # application
    "project.npda",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    #  2 factor authentication
    "django_otp.middleware.OTPMiddleware",
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR.joinpath("project/npda/templates"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# Session cookies
SESSION_COOKIE_SECURE = True  # enforces HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True  # cannot access session cookie on client-side using JS
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # session expires on browser close


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("NPDA_POSTGRES_DB_NAME"),
        "USER": os.environ.get("NPDA_POSTGRES_DB_USER"),
        "PASSWORD": os.environ.get("NPDA_POSTGRES_DB_PASSWORD"),
        "HOST": os.environ.get("NPDA_POSTGRES_DB_HOST"),
        "PORT": os.environ.get("NPDA_POSTGRES_DB_PORT"),
    }
}

# rest framework settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular schema settings
SPECTACULAR_SETTINGS = {
    "TITLE": "RCPCH National Paediatric Diabetes Audit API",
    "DESCRIPTION": "RCPCH National Paediatric Diabetes Audit.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
}

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # this is default
)


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "npda.NPDAUser"
LOGIN_URL = "two_factor:login"  # change LOGIN_URL to the 2fa one
LOGIN_REDIRECT_URL = "two_factor:profile"
LOGOUT_REDIRECT_URL = "two_factor:login"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    # {
    #     "NAME": "npda.validators.CapitalAndSymbolValidator",
    #     "OPTIONS": {
    #         "symbols": "!@£$%^&*()_-+=|~",
    #         "number_of_symbols": 1,
    #         "number_of_capitals": 1,
    #     },
    # },
    # {
    #     "NAME": "npda.validators.NumberValidator",  # must have one number
    # },
]

# Two Factor Authentication / One Time Password Settings (2FA / one-time login codes)
OTP_EMAIL_SUBJECT = "Your National Paediatric Diabetes Audit one-time login code"
OTP_EMAIL_BODY_TEMPLATE_PATH = "../templates/two_factor/email_token.txt"
OTP_EMAIL_BODY_HTML_TEMPLATE_PATH = "../templates/two_factor/email_token.html"
OTP_EMAIL_TOKEN_VALIDITY = 60 * 5  # default N(seconds) email token valid for

# EMAIL SETTINGS (SMTP)
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_DEFAULT_FROM_EMAIL")
SMTP_EMAIL_ENABLED = os.getenv("SMTP_EMAIL_ENABLED", "False") == "True"
logger.info("SMTP_EMAIL_ENABLED: %s", SMTP_EMAIL_ENABLED)
if SMTP_EMAIL_ENABLED is True:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("EMAIL_HOST_SERVER")
    EMAIL_PORT = os.environ.get("EMAIL_HOST_PORT")
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = True
    EMAIL_TIMEOUT = 10
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# logger.info("EMAIL_BACKEND: %s", EMAIL_BACKEND)

PASSWORD_RESET_TIMEOUT = os.environ.get(
    "PASSWORD_RESET_TIMEOUT", 259200
)  # Default: 259200 (3 days, in seconds)

SITE_CONTACT_EMAIL = os.environ.get("SITE_CONTACT_EMAIL")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = (str(BASE_DIR.joinpath("static")),)
STATIC_ROOT = str(BASE_DIR.joinpath("staticfiles"))
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_ROOT = os.path.join(BASE_DIR, "static/root")

SMTP_EMAIL_ENABLED = "False"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

USE_I18N = True

# The USE_L10N setting is deprecated. Starting with Django 5.0, localized formatting of data will always be enabled. For example Django will display numbers and dates using the format of the current locale.
# USE_L10N = True

USE_TZ = True
