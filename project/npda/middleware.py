# local storage for current user - will not work in async contexts
# This is used to track the user making changes in the admin interface as well as in the view by storing 
# the user in thread-local storage. 

from threading import local
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

class NPDAUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, 'user', None))
        set_current_request(request)
        response = self.get_response(request)
        
        # Clean up thread-local storage after request
        if hasattr(_user, 'value'):
            delattr(_user, 'value')
        if hasattr(_user, 'request'):
            delattr(_user, 'request')
            
        return response