from django.contrib import admin

# Register your models here.
# vehiculos/admin.py
from django.contrib import admin
from .models import Vehiculo, DocumentoVehiculo, RegistroAcceso

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('patente', 'tipo_vehiculo', 'marca', 'modelo', 'estado', 'fecha_ingreso')
    list_filter = ('estado', 'tipo_vehiculo', 'marca')
    search_fields = ('patente', 'numero_chasis', 'nombre_chofer')

@admin.register(DocumentoVehiculo)
class DocumentoVehiculoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'tipo_documento', 'fecha_subida')

@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'tipo_movimiento', 'fecha_hora', 'nombre_chofer', 'guardia')
    list_filter = ('tipo_movimiento', 'fecha_hora')
    search_fields = ('vehiculo__patente', 'nombre_chofer', 'guardia__username')
    date_hierarchy = 'fecha_hora'
    readonly_fields = ('fecha_hora',)