from django.contrib import admin

# Register your models here.
# mantenimientos/admin.py
from django.contrib import admin
from .models import Tarea, Pausa

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'vehiculo', 'prioridad', 'estado', 'mecanico_asignado', 'fecha_creacion')
    list_filter = ('estado', 'prioridad')
    search_fields = ('titulo', 'vehiculo__patente')

@admin.register(Pausa)
class PausaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'motivo', 'fecha_inicio', 'fecha_fin')
    list_filter = ('motivo',)