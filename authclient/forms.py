from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.admin.forms import AdminAuthenticationForm

from authclient.client import auth_client


class AdminAuthenticationForm(AdminAuthenticationForm):
    username = forms.CharField(label='Username', max_length=254)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super(AdminAuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:

            resource_token = auth_client.password_login.call(
                payload={'username': username, 'password': password},
                headers={'X-APPLICATION': settings.AUTH_API_TOKEN}
            )['resource_token']

            self.user_cache = authenticate(resource_token=resource_token)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': 'username'},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
