from django.contrib import admin
from .models import LogActividad

@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'usuario', 'accion', 'descripcion', 'ip_address')
    list_filter = ('accion', 'fecha_hora')
    search_fields = ('usuario__username', 'descripcion')
    readonly_fields = ('fecha_hora', 'usuario', 'accion', 'descripcion', 'ip_address')
