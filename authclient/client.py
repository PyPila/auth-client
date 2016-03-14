from django.conf import settings

from restservice.builder import Service


auth_client = Service(settings.AUTH_URL)
auth_client.add('password_login', 'post', '/login/password/')
auth_client.add('token_refresh', 'post', '/refresh/')
