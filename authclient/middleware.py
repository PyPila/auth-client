from requests.exceptions import HTTPError

from django.http import HttpResponse
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import load_backend
from django.contrib.auth.models import AnonymousUser
from django.utils.crypto import constant_time_compare

from authclient import (
    BACKEND_SESSION_KEY, HASH_SESSION_KEY, _get_user_session_key, SESSION_KEY
)
from authclient.models import AuthorizedApplication
from authclient.client import auth_client


class AuthorizedApplicationMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'app_auth_exempt', False):
            return None
        for path in settings.APP_EXEMPT_URLS:
            if request.path.startswith(path):
                return None

        api_token = request.META.get('HTTP_X_APPLICATION')
        if api_token:
            try:
                app = AuthorizedApplication.objects.get(api_token=api_token)
                request.application = app
                return None
            except AuthorizedApplication.DoesNotExist:
                pass
        return HttpResponse(status=401)


class JWTAuthMiddleware(object):

    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: self.get_user(request))

    def get_user(self, request, resource_token=None):
        user = None
        try:
            resource_token = resource_token or _get_user_session_key(request)
            backend_path = request.session[BACKEND_SESSION_KEY]
        except KeyError:
            pass
        else:
            if backend_path in settings.AUTHENTICATION_BACKENDS:
                backend = load_backend(backend_path)
                user = backend.authenticate(resource_token)
                if hasattr(user, 'get_session_auth_hash'):
                    session_hash = request.session.get(HASH_SESSION_KEY)
                    session_hash_verified = (
                        session_hash and constant_time_compare(
                            session_hash,
                            user.get_session_auth_hash()
                        )
                    )
                    if not session_hash_verified:
                        request.session.flush()
                        user = None

        return user or AnonymousUser()

    def process_response(self, request, response):
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
            except HTTPError as e:
                print(e.response.content)
            else:
                request.session[SESSION_KEY] = resource_token

        return response
