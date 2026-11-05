from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

schema_view = get_schema_view(
    openapi.Info(
        title='Librería API',
        default_version='v1',
        description=(
            'API REST para la gestión de usuarios de la Librería. '
            'Autenticación mediante JWT (SimpleJWT).'
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/v1/auth/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path(
        'api/v1/auth/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh',
    ),
    path('api/v1/auth/', include('users.urls')),
    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui',
    ),
    path(
        'swagger<format>/',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc',
    ),
]
