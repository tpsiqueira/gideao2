from django.urls import path, include
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from login_app.views import logout_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("admin_app.urls")),
    path("", include("monitor_app.urls")),
    path("login/", include("login_app.urls")),
    path("logout/", logout_view, name="logout"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
