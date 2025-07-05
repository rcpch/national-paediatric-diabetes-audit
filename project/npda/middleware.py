# local storage for current user - will not work in async contexts
# This is used to track the user making changes in the admin interface as well as in the view by storing 
# the user in thread-local storage. 

from threading import local
_user = local()

def set_current_user(user):
    _user.value = user

def get_current_user():
    return getattr(_user, 'value', None)

class NPDAUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, 'user', None))
        response = self.get_response(request)
        return response