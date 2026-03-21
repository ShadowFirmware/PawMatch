from django.contrib import admin
from .models import Mascota, FotoMascota, Preferencia


@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ['mascota_id', 'nombre', 'especie', 'raza', 'edad', 'género', 'dueño']
    list_filter = ['especie', 'género', 'edad']
    search_fields = ['nombre', 'especie', 'raza']
    readonly_fields = ['mascota_id']


@admin.register(FotoMascota)
class FotoMascotaAdmin(admin.ModelAdmin):
    list_display = ['foto_id', 'mascota', 'es_principal']
    list_filter = ['es_principal']
    search_fields = ['mascota__nombre']


@admin.register(Preferencia)
class PreferenciaAdmin(admin.ModelAdmin):
    list_display = ['pref_id', 'dueño', 'especie_pref', 'distancia_max']
    search_fields = ['dueño__nombre', 'dueño__email']
