from rest_framework.authentication import TokenAuthentication


class BearerTokenAuthentication(TokenAuthentication):
    """Acepta el prefijo 'Bearer' además del estándar 'Token' de DRF."""
    keyword = 'Bearer'
