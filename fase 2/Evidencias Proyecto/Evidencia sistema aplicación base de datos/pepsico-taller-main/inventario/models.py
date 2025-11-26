from django.db import models

# Create your models here.
# inventario/models.py
from django.db import models
from django.core.validators import MinValueValidator
from usuarios.models import Usuario
from mantenimientos.models import Tarea

class CategoriaRepuesto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Categoría de Repuesto'
        verbose_name_plural = 'Categorías de Repuestos'

class Repuesto(models.Model):
    ESTADO_CHOICES = (
        ('disponible', 'Disponible'),
        ('bajo_stock', 'Bajo Stock'),
        ('agotado', 'Agotado'),
        ('descontinuado', 'Descontinuado'),
    )
    
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    categoria = models.ForeignKey(CategoriaRepuesto, on_delete=models.PROTECT, verbose_name='Categoría')
    marca = models.CharField(max_length=100, blank=True)
    modelo_compatible = models.CharField(max_length=200, blank=True, verbose_name='Modelo Compatible')
    
    # Información de stock
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Stock Actual')
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)], verbose_name='Stock Mínimo')
    stock_maximo = models.IntegerField(default=100, validators=[MinValueValidator(0)], verbose_name='Stock Máximo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    
    # Información de precios
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio de Costo')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio de Venta')
    
    # Ubicación en bodega
    ubicacion_bodega = models.CharField(max_length=100, blank=True, verbose_name='Ubicación en Bodega')
    codigo_barras = models.CharField(max_length=100, blank=True, verbose_name='Código de Barras')
    
    # Información adicional
    proveedor = models.CharField(max_length=200, blank=True)
    tiempo_reposicion = models.IntegerField(default=7, help_text='Días estimados para reposición', verbose_name='Tiempo de Reposición')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Actualizar estado según stock
        if self.stock_actual <= 0:
            self.estado = 'agotado'
        elif self.stock_actual <= self.stock_minimo:
            self.estado = 'bajo_stock'
        else:
            self.estado = 'disponible'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def necesita_reposicion(self):
        return self.stock_actual <= self.stock_minimo
    
    @property
    def valor_total_inventario(self):
        return self.stock_actual * self.precio_costo

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = (
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferencia'),
    )
    
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    
    # Referencias - CORREGIDO
    tarea = models.ForeignKey('mantenimientos.Tarea', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos_inventario')
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='movimientos_inventario')
    
    # Información del movimiento
    motivo = models.TextField()
    numero_documento = models.CharField(max_length=100, blank=True, verbose_name='Número de Documento')
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Stock después del movimiento
    stock_anterior = models.IntegerField()
    stock_posterior = models.IntegerField()
    
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    fecha_documento = models.DateField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Solo para nuevos movimientos
            self.stock_anterior = self.repuesto.stock_actual
            
            if self.tipo_movimiento == 'entrada':
                self.stock_posterior = self.stock_anterior + self.cantidad
            else:  # salida, ajuste, transferencia
                self.stock_posterior = self.stock_anterior - self.cantidad
            
            # Actualizar stock del repuesto
            self.repuesto.stock_actual = self.stock_posterior
            self.repuesto.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.repuesto.codigo} - {self.cantidad}"

class AjusteInventario(models.Model):
    MOTIVO_AJUSTE = (
        ('diferencia_fisica', 'Diferencia Física'),
        ('robo', 'Robo o Pérdida'),
        ('dano', 'Daño o Deterioro'),
        ('caducidad', 'Caducidad'),
        ('conteo_fisico', 'Conteo Físico'),
        ('otro', 'Otro'),
    )
    
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad_fisica = models.IntegerField(verbose_name='Cantidad Física')
    cantidad_sistema = models.IntegerField(verbose_name='Cantidad en Sistema')
    diferencia = models.IntegerField(verbose_name='Diferencia')
    motivo = models.CharField(max_length=20, choices=MOTIVO_AJUSTE)
    motivo_otro = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_ajuste = models.DateTimeField(auto_now_add=True)
    fecha_conteo = models.DateField()
    
    def save(self, *args, **kwargs):
        self.diferencia = self.cantidad_fisica - self.cantidad_sistema
        super().save(*args, **kwargs)
        
        # Crear movimiento de ajuste automático
        if self.diferencia != 0:
            MovimientoInventario.objects.create(
                repuesto=self.repuesto,
                tipo_movimiento='ajuste',
                cantidad=abs(self.diferencia),
                usuario=self.usuario,
                motivo=f"Ajuste por {self.get_motivo_display()}: {self.observaciones}",
                stock_anterior=self.cantidad_sistema,
                stock_posterior=self.cantidad_fisica
            )
    
    def __str__(self):
        return f"Ajuste {self.repuesto.codigo} - Diferencia: {self.diferencia}"

class PedidoRepuesto(models.Model):
    ESTADO_PEDIDO = (
        ('pendiente', 'Pendiente'),
        ('ordenado', 'Ordenado'),
        ('parcial', 'Recibido Parcialmente'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    )
    
    codigo_pedido = models.CharField(max_length=50, unique=True, verbose_name='Código de Pedido')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad_solicitada = models.IntegerField(validators=[MinValueValidator(1)])
    cantidad_recibida = models.IntegerField(default=0)
    proveedor = models.CharField(max_length=200)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_estimada_entrega = models.DateField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    
    solicitante = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pedidos_solicitados')
    observaciones = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.costo_unitario and self.cantidad_solicitada:
            self.costo_total = self.costo_unitario * self.cantidad_solicitada
        
        # Generar código de pedido automáticamente
        if not self.codigo_pedido:
            from django.utils import timezone
            fecha = timezone.now().strftime('%Y%m%d')
            ultimo_pedido = PedidoRepuesto.objects.filter(
                codigo_pedido__startswith=f'PED-{fecha}'
            ).count()
            self.codigo_pedido = f'PED-{fecha}-{ultimo_pedido + 1:03d}'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo_pedido} - {self.repuesto.nombre}"