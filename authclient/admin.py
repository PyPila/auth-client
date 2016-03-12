from django.http import HttpResponseRedirect
from django.contrib.admin import AdminSite
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group

from authclient.models import AuthorizedApplication
from authclient.forms import AdminAuthenticationForm
from authclient.views import login as login_view


class AuthAdminSite(AdminSite):
    site_header = 'Amok administration'
    login_form = AdminAuthenticationForm

    @never_cache
    def login(self, request, extra_context=None):
        """
        Displays the login form for the given HttpRequest.
        """
        if request.method == 'GET' and self.has_permission(request):
            # Already logged-in, redirect to admin index
            index_path = reverse('admin:index', current_app=self.name)
            return HttpResponseRedirect(index_path)

        context = dict(
            self.each_context(request),
            title='Log in',
            app_path=request.get_full_path(),
        )
        if (
            REDIRECT_FIELD_NAME not in request.GET and
            REDIRECT_FIELD_NAME not in request.POST
        ):
            context[REDIRECT_FIELD_NAME] = reverse(
                'admin:index',
                current_app=self.name
            )
        context.update(extra_context or {})

        defaults = {
            'extra_context': context,
            'authentication_form': self.login_form or AdminAuthenticationForm,
            'template_name': self.login_template or 'admin/login.html',
        }
        request.current_app = self.name
        return login_view(request, **defaults)


site = AuthAdminSite(name='admin')
site.register(AuthorizedApplication)
site.register(User)
site.register(Group)
