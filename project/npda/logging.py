# local storage for current user - will not work in async contexts
# This is used to track the user making changes in the admin interface as well as in the view by storing 
# the user in thread-local storage. 

import logging
from datetime import datetime
from threading import local
from django.conf import settings

request_logger = logging.getLogger(__name__)

_user = local()

def set_current_user(user):
    _user.value = user

def get_current_user():
    return getattr(_user, 'value', None)

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
        set_current_user(getattr(request, 'user', None))
        set_current_request(request)
        response = self.get_response(request)
        return response

class NPDARequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # The dev server already does request logging
        if not settings.DEBUG:
            # This replaces the old gunicorn request logging which used this format string
            # %({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"
            gunicorn_formatted_datetime = datetime.now().astimezone().strftime("%d/%m/%y:%H:%M:%S %z")

            request_logger.info(f"{request.META.get('HTTP_X_FORWARDED_FOR', '')} - {get_current_user()} {gunicorn_formatted_datetime} \"{request.method} {request.get_full_path()}\" {response.status_code} {response.get('Content-Length', "-")} \"{request.META.get('HTTP_REFERER', '-')}\" \"{request.META.get('HTTP_USER_AGENT', '-')}\"")
            
        return response
