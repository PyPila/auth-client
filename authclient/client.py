from django.conf import settings

from pyservice.builder import Service


auth_client = Service(settings.AUTH_URL)
auth_client.add('password_login', 'post', '/login/password/')
