=====
amok auth-client
=====

VERY EXPERIMENTAL - not production ready and under development.

Simple client used in django porjects that need to use amok auth as the
authentiacation service.

Quick start
-----------

1. Add "authclient" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'authclient',
    ]

2. Change the admin site from the default to the authclient one::

    from authclient import admin

    url(r'^admin/', admin.site.urls),

3. Replace the standard Django authentication middleware with this::

    MIDDLEWARE_CLASSES = [
        ...
        'authclient.middleware.JWTAuthMiddleware',
        ...
    ]

4. [Optional] If willing to use the app authorization add the following as your first middleware::

    MIDDLEWARE_CLASSES = [
        'authclient.middleware.AuthorizedApplicationMiddleware',
        ...
    ]

5. Run `python manage.py migrate` to create the authclient models.
