import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger('pawmatch.errors')


def custom_exception_handler(exc, context):
    """
    Maneja excepciones no controladas:
    - En DEBUG: devuelve el detalle completo.
    - En producción: devuelve mensaje genérico y loguea internamente.
    """
    response = exception_handler(exc, context)

    if response is None:
        # Excepción no manejada por DRF
        logger.error(
            'Excepción no manejada en %s: %s',
            context.get('view', '?'),
            exc,
            exc_info=True,
        )
        if settings.DEBUG:
            return Response(
                {'error': 'Error interno del servidor', 'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
