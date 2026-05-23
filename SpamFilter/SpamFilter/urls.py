from django.contrib import admin
from django.urls import path, re_path
from Filter.views import menu, predict, get_result
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView
from rest_framework import permissions

app_name = "Filter"

schema_view = get_schema_view(
    openapi.Info(
        title="Spam Filter API",
        default_version='v1',
        description="API для фильтрации спама",
        terms_of_service="https://example.com/terms/",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("/", menu, name="menu"),
    path("", menu, name="menu"),
    path("predict/", predict, name="predict"),
    path("result/<str:task_id>/", get_result, name="get_result"),   # новый маршрут
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]