from django.contrib import admin
from .models import Dueño

DUENO_ID_FIELD = 'dueño_id'


@admin.register(Dueño)
class DuenoAdmin(admin.ModelAdmin):
    list_display = [DUENO_ID_FIELD, 'nombre', 'email', 'fecha_registro', 'is_active', 'ciudad', 'estado']
    list_filter = ['is_active', 'fecha_registro', 'genero', 'ciudad', 'estado']
    search_fields = ['nombre', 'email', 'ciudad', 'estado']
    readonly_fields = [DUENO_ID_FIELD, 'fecha_registro']
    fieldsets = (
        ('Información Básica', {
            'fields': (DUENO_ID_FIELD, 'nombre', 'email', 'ubicación', 'fecha_registro')
        }),
        ('Perfil', {
            'fields': ('foto_perfil', 'telefono', 'biografia', 'fecha_nacimiento', 'genero', 
                      'ciudad', 'estado', 'pais', 'mostrar_telefono', 'mostrar_email')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )
