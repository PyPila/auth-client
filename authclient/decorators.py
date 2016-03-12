from functools import wraps


def app_auth_exempt(function=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        _wrapped.app_auth_exempt = True
        return _wrapped

    if function:
        return decorator(function)
    return decorator
