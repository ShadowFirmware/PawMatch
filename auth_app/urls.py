from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DueñoViewSet, PerfilViewSet, login_view, register_view, logout_view, 
    google_auth_view, facebook_auth_view,
    password_reset_request_view, password_reset_verify_view, password_reset_confirm_view
)

router = DefaultRouter()
router.register(r'dueños', DueñoViewSet, basename='dueño')
router.register(r'perfiles', PerfilViewSet, basename='perfil')

urlpatterns = [
    path('auth/login/',    login_view,    name='login'),
    path('auth/logout/',   logout_view,   name='logout'),
    path('auth/register/', register_view, name='register'),
    path('auth/google/',   google_auth_view,   name='google-auth'),
    path('auth/facebook/', facebook_auth_view, name='facebook-auth'),
    
    # Recuperación de contraseña
    path('auth/password-reset/request/', password_reset_request_view, name='password-reset-request'),
    path('auth/password-reset/verify/', password_reset_verify_view, name='password-reset-verify'),
    path('auth/password-reset/confirm/', password_reset_confirm_view, name='password-reset-confirm'),
    
    path('', include(router.urls)),
]
