from functools import update_wrapper

from django.http import HttpResponseRedirect
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.conf import settings
from django.conf.urls import url, include
from django.contrib.contenttypes import views as contenttype_views
from django.views.generic import RedirectView

from authclient.models import AuthorizedApplication
from authclient.forms import AdminAuthenticationForm
from authclient.views import login as login_view
from authclient.decorators import app_auth_exempt, refresh_jwt


class AuthAdminSite(admin.AdminSite):
    site_header = 'Amok administration'
    login_form = AdminAuthenticationForm

    def register(self, model_or_iterable, admin_class=None, **options):
        if not admin_class:
            admin_class = ModelAdmin

        super(AuthAdminSite, self).register(
            model_or_iterable, admin_class, **options
        )

    @never_cache
    def login(self, request, extra_context=None):
        """
        Displays the login form for the given HttpRequest.
        """
        if request.method == 'GET' and self.has_permission(request):
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

    def get_urls(self):
        if settings.DEBUG:
            self.check_dependencies()

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            wrapper.admin_site = self
            wrapper = app_auth_exempt(wrapper)
            wrapper = refresh_jwt(wrapper)
            return update_wrapper(wrapper, view)

        urlpatterns = [
            url(r'^$', wrap(self.index), name='index'),
            url(r'^login/$', app_auth_exempt(self.login), name='login'),
            url(r'^logout/$', wrap(self.logout), name='logout'),
            url(
                r'^password_change/$',
                wrap(self.password_change, cacheable=True),
                name='password_change'
            ),
            url(
                r'^password_change/done/$',
                wrap(self.password_change_done, cacheable=True),
                name='password_change_done'
            ),
            url(
                r'^jsi18n/$',
                wrap(self.i18n_javascript, cacheable=True),
                name='jsi18n'
            ),
            url(
                r'^r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                wrap(contenttype_views.shortcut),
                name='view_on_site'
            ),
        ]

        valid_app_labels = []
        for model, model_admin in self._registry.items():
            urlpatterns += [
                url(r'^%s/%s/' % (
                    model._meta.app_label, model._meta.model_name
                ), include(model_admin.urls)),
            ]
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

        if valid_app_labels:
            regex = r'^(?P<app_label>' + '|'.join(valid_app_labels) + ')/$'
            urlpatterns += [
                url(regex, wrap(self.app_index), name='app_list'),
            ]
        return urlpatterns


site = AuthAdminSite(name='admin')


class ModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            wrapper = app_auth_exempt(wrapper)
            wrapper = refresh_jwt(wrapper)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        urlpatterns = [
            url(
                r'^$', wrap(self.changelist_view),
                name='%s_%s_changelist' % info
            ),
            url(
                r'^add/$', wrap(self.add_view),
                name='%s_%s_add' % info
            ),
            url(
                r'^(.+)/history/$', wrap(self.history_view),
                name='%s_%s_history' % info
            ),
            url(
                r'^(.+)/delete/$', wrap(self.delete_view),
                name='%s_%s_delete' % info
            ),
            url(
                r'^(.+)/change/$', wrap(self.change_view),
                name='%s_%s_change' % info
            ),
            url(r'^(.+)/$', wrap(RedirectView.as_view(
                pattern_name='%s:%s_%s_change' % (
                    (self.admin_site.name,) + info
                )
            ))),
        ]
        return urlpatterns


class AuthorizedApplicationAdmin(ModelAdmin):
    list_display = ('name', 'api_token', )


site.register(AuthorizedApplication, AuthorizedApplicationAdmin)
