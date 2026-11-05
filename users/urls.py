from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MeView, UserApiViewSet

router = DefaultRouter()
router.register(r'users', UserApiViewSet, basename='users')

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
