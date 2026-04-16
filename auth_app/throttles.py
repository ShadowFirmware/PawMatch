from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Máximo 5 intentos de login por minuto por IP."""
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    """Máximo 3 registros por minuto por IP."""
    scope = 'register'


class ReporteRateThrottle(UserRateThrottle):
    """Máximo 10 reportes por hora por usuario autenticado."""
    scope = 'reporte'
