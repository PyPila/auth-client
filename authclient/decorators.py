import logging
from functools import wraps
from requests.exceptions import HTTPError

from django.utils.decorators import available_attrs
from django.conf import settings

from authclient import _get_user_session_key, SESSION_KEY
from authclient.client import auth_client

logger = logging.getLogger('authclient')


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


def refresh_jwt(view_func):
    """
    Decorator that adds headers to a response so that it will
    never be cached.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        try:
            resource_token = _get_user_session_key(request)
        except KeyError:
            pass
        else:
            try:
                resource_token = auth_client.token_refresh.call(
                    payload={'token': resource_token},
                    headers={'X-APPLICATION': settings.AUTH_API_TOKEN},
                )['resource_token']
            except HTTPError:
                logger.debug('Failed to refresh the JWT.')
            else:
                request.session[SESSION_KEY] = resource_token

        return response
    return _wrapped_view_func
