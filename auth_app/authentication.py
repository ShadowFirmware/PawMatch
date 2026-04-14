from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

# Días de vida del token (configurable en settings)
TOKEN_EXPIRY_DAYS = getattr(settings, 'TOKEN_EXPIRY_DAYS', 7)


class BearerTokenAuthentication(TokenAuthentication):
    """Acepta el prefijo 'Bearer' y rechaza tokens expirados."""
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Token inválido o expirado.')

        if not token.user.is_active:
            raise AuthenticationFailed('Cuenta inactiva o deshabilitada.')

        # Verificar expiración por tiempo absoluto (7 días desde creación)
        if timezone.now() > token.created + timedelta(days=TOKEN_EXPIRY_DAYS):
            token.delete()
            raise AuthenticationFailed('Sesión expirada. Inicia sesión nuevamente.')

        return (token.user, token)
