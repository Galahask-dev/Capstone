from django.contrib import admin

# Register your models here.
# inventario/admin.py
from django.contrib import admin
from .models import CategoriaRepuesto, Repuesto, MovimientoInventario, AjusteInventario, PedidoRepuesto

@admin.register(CategoriaRepuesto)
class CategoriaRepuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'estado', 'precio_costo', 'precio_venta')
    list_filter = ('estado', 'categoria', 'marca')
    search_fields = ('codigo', 'nombre', 'modelo_compatible')
    readonly_fields = ('estado', 'fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'marca', 'modelo_compatible')
        }),
        ('Gestión de Stock', {
            'fields': ('stock_actual', 'stock_minimo', 'stock_maximo', 'estado', 'ubicacion_bodega')
        }),
        ('Información de Precios', {
            'fields': ('precio_costo', 'precio_venta', 'proveedor')
        }),
        ('Información Adicional', {
            'fields': ('codigo_barras', 'tiempo_reposicion', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('repuesto', 'tipo_movimiento', 'cantidad', 'stock_anterior', 'stock_posterior', 'usuario', 'fecha_movimiento')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    search_fields = ('repuesto__codigo', 'repuesto__nombre', 'motivo')
    readonly_fields = ('stock_anterior', 'stock_posterior', 'fecha_movimiento')

@admin.register(AjusteInventario)
class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = ('repuesto', 'cantidad_fisica', 'cantidad_sistema', 'diferencia', 'motivo', 'fecha_ajuste')
    list_filter = ('motivo', 'fecha_ajuste')
    search_fields = ('repuesto__codigo', 'repuesto__nombre')

@admin.register(PedidoRepuesto)
class PedidoRepuestoAdmin(admin.ModelAdmin):
    list_display = ('codigo_pedido', 'repuesto', 'cantidad_solicitada', 'cantidad_recibida', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('codigo_pedido', 'repuesto__codigo', 'repuesto__nombre')