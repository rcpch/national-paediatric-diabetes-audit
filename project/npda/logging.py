# local storage for current user - will not work in async contexts
# This is used to track the user making changes in the admin interface as well as in the view by storing
# the user in thread-local storage.

import logging
import resource
from datetime import datetime
from threading import local
from timeit import default_timer as timer

from django.conf import settings

request_logger = logging.getLogger("npda_request_log")

_user = local()


def set_current_user(user):
    _user.value = user


def get_current_user():
    return getattr(_user, "value", None)


def set_current_request(request):
    """
    Store the current request in thread-local storage.
    """
    _user.request = request


def get_current_request():
    """
    Returns the current request object if available, otherwise None.
    This is useful for accessing the request in signals or other contexts.
    """
    try:
        return _user.request
    except AttributeError:
        return None


class NPDACustomLoggingAttributesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, "user", None))
        set_current_request(request)

        response = self.get_response(request)

        # Clean up thread-local storage after request
        if hasattr(_user, "value"):
            delattr(_user, "value")
        if hasattr(_user, "request"):
            delattr(_user, "request")

        return response


class NPDARequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = timer()

        rss_start = None
        if settings.ENABLE_MEMORY_LOGGING:
            rss_start = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        response = self.get_response(request)

        end = timer()

        duration = end - start
        duration_ms = round(duration * 1000)

        rss_end = None
        if settings.ENABLE_MEMORY_LOGGING:
            rss_end = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        # The dev server already does request logging
        if settings.ENABLE_REQUEST_LOGGING:
            # This replaces the old gunicorn request logging which used this date format string
            gunicorn_formatted_datetime = (
                datetime.now().astimezone().strftime("%d/%m/%y:%H:%M:%S %z")
            )

            username_to_log = "-" if request.user.is_anonymous else request.user.email

            rss_message = ""
            if (
                settings.ENABLE_MEMORY_LOGGING
                and rss_start is not None
                and rss_end is not None
            ):
                rss_message = f" rss_start={rss_start} rss_end={rss_end} rss_diff={rss_end - rss_start}"

            request_logger.info(
                f'{request.META.get("HTTP_X_FORWARDED_FOR", "")} - {username_to_log} [{gunicorn_formatted_datetime}] "{request.method} {request.get_full_path()}" {response.status_code} {response.get("Content-Length", "-")} "{request.META.get("HTTP_REFERER", "-")}" "{request.META.get("HTTP_USER_AGENT", "-")}" {duration_ms}{rss_message}'
            )

        return response
