# middleware.py
from threading import local

_thread_locals = local()

def get_current_user():
    """Ultra-fast user lookup"""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only store user if authenticated (saves memory)
        if request.user.is_authenticated:
            _thread_locals.user = request.user
        else:
            _thread_locals.user = None
        
        response = self.get_response(request)
        
        
        return response