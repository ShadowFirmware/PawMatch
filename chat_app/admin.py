from django.contrib import admin
from .models import Mensaje


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ['msg_id', 'match', 'remitente', 'fecha_envío', 'leído']
    list_filter = ['leído', 'fecha_envío']
    search_fields = ['remitente__nombre', 'contenido']
    readonly_fields = ['msg_id', 'fecha_envío']
