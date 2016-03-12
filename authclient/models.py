from django.db import models


class AuthorizedApplication(models.Model):

    api_token = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)


class JWTUser(object):

    is_active = True

    is_superuser = False
    is_staff = False

    groups = {}
    user_permissions = {}

    def __init__(self, resource_token, payload):
        self._user_permissions = set(payload['perms'])
        self.username = payload['username']
        self.is_superuser = payload['is_superuser']
        self.is_staff = payload['is_staff']
        self.pk = payload['pk']
        self.resource_token = resource_token

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_group_permissions(self, obj=None):
        return self.get_all_permissions(obj)

    def get_all_permissions(self, obj=None):
        return self._user_permissions

    def has_perm(self, perm, obj=None):
        return perm in self.get_all_permissions()

    def has_perms(self, perm_list, obj=None):
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        if self.is_active and self.is_superuser:
            return True
        if not self.is_active:
            return False
        for perm in self.get_all_permissions(self):
            if perm[:perm.index('.')] == app_label:
                return True
        return False

    def save(self, *args, **kwargs):
        pass

    @property
    def _meta(self):
        class Meta:
            pk_field = models.CharField()
            pk_field.attname = 'resource_token'
            pk = pk_field
        return Meta
