from django.contrib import admin
from .models import Match, Reporte


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['match_id', 'mascota1', 'mascota2', 'estado', 'fecha_match']
    list_filter = ['estado', 'fecha_match']
    search_fields = ['mascota1__nombre', 'mascota2__nombre']
    readonly_fields = ['match_id', 'fecha_match']


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'dueño', 'mascota', 'fecha_reporte']
    list_filter = ['fecha_reporte']
    search_fields = ['dueño__nombre', 'mascota__nombre']
    readonly_fields = ['report_id', 'fecha_reporte']
