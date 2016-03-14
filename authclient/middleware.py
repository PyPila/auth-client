import logging
from django.http import HttpResponse
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import load_backend
from django.contrib.auth.models import AnonymousUser
from django.utils.crypto import constant_time_compare

from authclient import (
    BACKEND_SESSION_KEY, HASH_SESSION_KEY, _get_user_session_key,
)
from authclient.models import AuthorizedApplication

logger = logging.getLogger('authclient')


class AuthorizedApplicationMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        if getattr(view_func, 'app_auth_exempt', False):
            return None

        api_token = request.META.get('HTTP_X_APPLICATION')
        if api_token:
            try:
                app = AuthorizedApplication.objects.get(api_token=api_token)
                request.application = app
                return None
            except AuthorizedApplication.DoesNotExist:
                pass
        logger.info('Unauthenticated application.')
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
