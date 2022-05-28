from functools import update_wrapper

from django.contrib import admin
from django.http import Http404
from django.urls import path
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.defaults import page_not_found


class CustomAdminSite(admin.AdminSite):
    """Custom admin site which returns a 404 for non-staff users."""

    def admin_view(self, view, cacheable=False):
        """Decorator to create an admin view attached to this ``AdminSite``."""

        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                raise Http404()
            return view(request, *args, **kwargs)

        if not cacheable:
            inner = never_cache(inner)

        if not getattr(view, "csrf_exempt", False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def get_urls(self):
        urlpatterns = super().get_urls()
        urlpatterns = [
            path("login/", page_not_found, kwargs={"exception": Http404()})
        ] + urlpatterns

        return urlpatterns
