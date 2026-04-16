"""
Funciones auxiliares para registrar eventos en la bitácora.
"""
import ipaddress
import logging

security_log = logging.getLogger('pawmatch.security')


def get_client_ip(request):
    """
    Devuelve la IP real del cliente.

    Solo usa X-Forwarded-For si TRUST_X_FORWARDED_FOR=True en settings,
    evitando que cualquier cliente falsifique su IP en los logs y en el
    rate-limiting basado en IP.
    """
    from django.conf import settings
    trust_proxy = getattr(settings, 'TRUST_X_FORWARDED_FOR', False)

    if trust_proxy:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded:
            # Tomar solo la primera IP de la cadena y validar formato
            candidate = x_forwarded.split(',')[0].strip()
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass  # IP malformada → caer al REMOTE_ADDR

    return request.META.get('REMOTE_ADDR', '')


def log_event(accion, request=None, usuario=None, detalles=None):
    """
    Guarda un evento en la base de datos (BitacoraEvento) y en el log de seguridad.
    Es seguro llamarlo desde cualquier view; los errores no interrumpen el flujo principal.

    Se registra el PK del usuario (nunca el email) para evitar PII en los archivos de log.
    """
    from .models import BitacoraEvento

    ip = get_client_ip(request) if request else None
    user = usuario or (request.user if request and request.user.is_authenticated else None)
    extra = detalles or {}

    try:
        BitacoraEvento.objects.create(
            accion=accion,
            usuario=user,
            ip_address=ip,
            detalles=extra,
        )
    except Exception as exc:
        security_log.error('No se pudo guardar BitacoraEvento: %s', exc)

    # Usar PK en lugar de email para no escribir PII en el archivo de log
    user_ref = getattr(user, 'pk', 'anónimo')
    security_log.info(
        'EVENTO=%s usuario_id=%s ip=%s detalles=%s',
        accion,
        user_ref,
        ip,
        extra,
    )
