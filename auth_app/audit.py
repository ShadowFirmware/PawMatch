"""
Funciones auxiliares para registrar eventos en la bitácora.
"""
import logging

security_log = logging.getLogger('pawmatch.security')


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_event(accion, request=None, usuario=None, detalles=None):
    """
    Guarda un evento en la base de datos (BitacoraEvento) y en el log de seguridad.
    Es seguro llamarlo desde cualquier view; los errores no interrumpen el flujo principal.
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

    security_log.info(
        'EVENTO=%s usuario=%s ip=%s detalles=%s',
        accion,
        getattr(user, 'email', 'anónimo'),
        ip,
        extra,
    )
