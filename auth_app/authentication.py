from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

TOKEN_EXPIRY_DAYS = getattr(settings, 'TOKEN_EXPIRY_DAYS', 7)
INACTIVITY_TIMEOUT_MINUTES = getattr(settings, 'INACTIVITY_TIMEOUT_MINUTES', 5)


class BearerTokenAuthentication(TokenAuthentication):
    """
    Acepta el prefijo 'Bearer' y aplica dos controles de sesión:
      1. Expiración absoluta: el token expira N días después de su creación.
      2. Cierre por inactividad: el token expira si no se usó en los últimos
         INACTIVITY_TIMEOUT_MINUTES minutos.
    """
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        from .models import TokenActividad

        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed('Token inválido o expirado.')

        if not token.user.is_active:
            raise AuthenticationFailed('Cuenta inactiva o deshabilitada.')

        now = timezone.now()

        # ── 1. Expiración absoluta (7 días desde creación) ────────────────────
        if now > token.created + timedelta(days=TOKEN_EXPIRY_DAYS):
            token.delete()
            raise AuthenticationFailed('Sesión expirada. Inicia sesión nuevamente.')

        # ── 2. Cierre por inactividad ─────────────────────────────────────────
        actividad, creada = TokenActividad.objects.get_or_create(token=token)

        if not creada:
            limite_inactividad = now - timedelta(minutes=INACTIVITY_TIMEOUT_MINUTES)
            if actividad.ultima_actividad < limite_inactividad:
                token.delete()
                raise AuthenticationFailed('Sesión cerrada por inactividad.')

        # Actualizar marca de actividad en cada request autenticado
        TokenActividad.objects.filter(token=token).update(ultima_actividad=now)

        return (token.user, token)
