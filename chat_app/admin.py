from django.contrib import admin
from .models import Mensaje

FECHA_ENVIO_FIELD = 'fecha_envío'


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ['msg_id', 'match', 'remitente', FECHA_ENVIO_FIELD, 'leído']
    list_filter = ['leído', FECHA_ENVIO_FIELD]
    search_fields = ['remitente__nombre', 'contenido']
    readonly_fields = ['msg_id', FECHA_ENVIO_FIELD]
