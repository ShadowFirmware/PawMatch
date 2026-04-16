"""
Middleware de cabeceras de seguridad HTTP para PawMatch.
Agrega Content-Security-Policy y otros headers faltantes en SecurityMiddleware.
"""


class SecurityHeadersMiddleware:
    """
    Agrega cabeceras de seguridad HTTP a todas las respuestas.
    Complementa las cabeceras que Django no cubre de forma nativa.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy
        # La API devuelve JSON; se bloquea todo salvo lo estrictamente necesario.
        # frame-ancestors 'none' reemplaza X-Frame-Options para CSP nivel 2+.
        response['Content-Security-Policy'] = (
            "default-src 'none'; "
            "script-src 'none'; "
            "style-src 'none'; "
            "img-src 'self' data:; "
            "font-src 'none'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'"
        )

        # Ocultar información del servidor
        response['Server'] = 'PawMatch'

        # Política de referrer
        response['Referrer-Policy'] = 'no-referrer'

        # Política de permisos (bloquear APIs del navegador no necesarias)
        response['Permissions-Policy'] = (
            'geolocation=(), camera=(), microphone=(), payment=()'
        )

        return response
