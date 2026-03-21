from django.contrib import admin
from .models import Dueño


@admin.register(Dueño)
class DueñoAdmin(admin.ModelAdmin):
    list_display = ['dueño_id', 'nombre', 'email', 'fecha_registro', 'is_active', 'ciudad', 'estado']
    list_filter = ['is_active', 'fecha_registro', 'genero', 'ciudad', 'estado']
    search_fields = ['nombre', 'email', 'ciudad', 'estado']
    readonly_fields = ['dueño_id', 'fecha_registro']
    fieldsets = (
        ('Información Básica', {
            'fields': ('dueño_id', 'nombre', 'email', 'ubicación', 'fecha_registro')
        }),
        ('Perfil', {
            'fields': ('foto_perfil', 'telefono', 'biografia', 'fecha_nacimiento', 'genero', 
                      'ciudad', 'estado', 'pais', 'mostrar_telefono', 'mostrar_email')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
    )
