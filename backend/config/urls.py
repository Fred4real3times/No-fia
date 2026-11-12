from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.api.auth_views import LoginView, MeView, RegisterView
from apps.api.views import LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", include("apps.api.health_urls")),
    path("api/v1/auth/register/", RegisterView.as_view(), name="api-register"),
    path("api/v1/auth/login/", LoginView.as_view(), name="api-login"),
    path("api/v1/auth/me/", MeView.as_view(), name="api-me"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="api-logout"),
    path("api/v1/", include("apps.api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
