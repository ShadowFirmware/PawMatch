from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DueñoViewSet, PerfilViewSet, login_view, register_view, logout_view, google_auth_view, facebook_auth_view

router = DefaultRouter()
router.register(r'dueños', DueñoViewSet, basename='dueño')
router.register(r'perfiles', PerfilViewSet, basename='perfil')

urlpatterns = [
    path('auth/login/',    login_view,    name='login'),
    path('auth/logout/',   logout_view,   name='logout'),
    path('auth/register/', register_view, name='register'),
    path('auth/google/',   google_auth_view,   name='google-auth'),
    path('auth/facebook/', facebook_auth_view, name='facebook-auth'),
    path('', include(router.urls)),
]
