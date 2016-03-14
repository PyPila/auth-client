import jwt

from django.conf import settings

from authclient.models import JWTUser


class JWTBackend(object):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, resource_token, **kwargs):
        try:
            return JWTUser(resource_token, self.jwt_decode(resource_token))
        except jwt.exceptions.ExpiredSignatureError:
            return None

    def jwt_decode(self, token):
        options = {
            'verify_exp': settings.AUTH_JWT_VERIFY_EXPIRATION,
        }

        return jwt.decode(
            token,
            settings.AUTH_JWT_PUBLIC_KEY,
            settings.AUTH_JWT_VERIFY,
            options=options,
            leeway=settings.AUTH_JWT_LEEWAY,
            audience=settings.AUTH_JWT_AUDIENCE,
            issuer=settings.AUTH_JWT_ISSUER,
            algorithms=[settings.AUTH_JWT_ALGORITHM]
        )

    def get_user_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings the user `user_obj` has from their
        `user_permissions`.
        """
        return user_obj.user_permissions

    def get_group_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings the user `user_obj` has from the
        groups they belong.
        """
        return self.get_user_permissions(user_obj, obj)

    def get_all_permissions(self, user_obj, obj=None):
        if (
            not user_obj.is_active or
            user_obj.is_anonymous() or
            obj is not None or
            not isinstance(user_obj, JWTUser)
        ):
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = self.get_group_permissions(user_obj)
        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        return perm in self.get_all_permissions(user_obj, obj)

    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.
        """
        if not user_obj.is_active:
            return False
        for perm in self.get_all_permissions(user_obj):
            if perm[:perm.index('.')] == app_label:
                return True
        return False

    def get_user(self, resource_token):
        return self.authenticate(resource_token)
