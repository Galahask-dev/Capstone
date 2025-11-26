

# Create your models here.
# vehiculos/models.py
from django.db import models
from usuarios.models import Usuario

class Vehiculo(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente de Aprobación'),
        ('ingresado', 'Ingresado'),
        ('diagnostico', 'En Diagnóstico'),
        ('reparacion', 'En Reparación'),
        ('listo', 'Listo para Retiro'),
        ('entregado', 'Entregado'),
        ('rechazado', 'Ingreso Rechazado'),
    )
    
    TIPOS_VEHICULO = (
        ('camion', 'Camión'),
        ('camion_dts', 'Camión DTS'),
        ('camion_cstore', 'Camión Cstore'),
        ('furgon', 'Furgón'),
        ('pickup', 'Pickup'),
        ('automovil', 'Automóvil'),
        ('maquinaria', 'Maquinaria'),
        ('funcional_flota', 'Funcional Flota'),
        ('merchandising', 'Merchandising'),
    )
    
    patente = models.CharField(max_length=10, unique=True)
    tipo_vehiculo = models.CharField(max_length=50, choices=TIPOS_VEHICULO)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.IntegerField()
    flota = models.CharField(max_length=100, blank=True, null=True)
    numero_chasis = models.CharField(max_length=50, blank=True)
    kilometraje = models.IntegerField(default=0, null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    # Información del chofer - MEJORADO
    nombre_chofer = models.CharField(max_length=100, blank=True)
    telefono_chofer = models.CharField(max_length=15, blank=True)
    empresa_chofer = models.CharField(max_length=100, blank=True)
    chofer_asignado = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'rol': 'chofer'},
        related_name='vehiculos_como_chofer'  # ← CAMBIADO: nombre único
    )
    
    # Estado y tracking
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ingresado')
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(blank=True, null=True)
    
    # Información del ingreso
    motivo_ingreso = models.TextField()
    observaciones_ingreso = models.TextField(blank=True)
    
    # Responsables - CORREGIR related_name
    guardia_ingreso = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='vehiculos_ingresados'  # ← Este está bien
    )
    mecanico_asignado = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='vehiculos_como_mecanico'  # ← CAMBIADO: nombre único
    )
    
    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"
    
    def save(self, *args, **kwargs):
        # Auto-completar nombre_chofer si hay chofer_asignado
        if self.chofer_asignado and not self.nombre_chofer:
            self.nombre_chofer = self.chofer_asignado.get_full_name() or self.chofer_asignado.username
        super().save(*args, **kwargs)

# vehiculos/models.py (AGREGAR al final)
class DocumentoVehiculo(models.Model):
    TIPO_DOCUMENTO = (
        ('permiso_circulacion', 'Permiso de Circulación'),
        ('seguro_soap', 'Seguro SOAP'),
        ('revision_tecnica', 'Revisión Técnica'),
        ('foto_ingreso', 'Foto de Ingreso'),
        ('foto_salida', 'Foto de Salida'),
        ('informe_siniestro', 'Informe de Siniestro'),
        ('orden_trabajo', 'Orden de Trabajo'),
        ('otro', 'Otro'),
    )
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=50, choices=TIPO_DOCUMENTO)
    archivo = models.FileField(upload_to='documentos_vehiculos/')
    nombre_archivo = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    
    def save(self, *args, **kwargs):
        if not self.nombre_archivo and self.archivo:
            self.nombre_archivo = self.archivo.name
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.vehiculo.patente}"
    
    @property
    def esta_vencido(self):
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento < timezone.now().date()
        return False


class Siniestro(models.Model):
    ESTADO_SINIESTRO = (
        ('reportado', 'Reportado'),
        ('en_evaluacion', 'En Evaluación'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('completado', 'Completado'),
    )
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='siniestros')
    numero_siniestro = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    fecha_siniestro = models.DateTimeField()
    lugar_siniestro = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_SINIESTRO, default='reportado')
    
    # Información del seguro
    compañia_seguro = models.CharField(max_length=100, blank=True)
    numero_poliza = models.CharField(max_length=100, blank=True)
    
    # Responsables
    reportado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT, related_name='siniestros_reportados')
    evaluador = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='siniestros_evaluados')
    
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generar número de siniestro automáticamente si no existe
        if not self.numero_siniestro:
            from django.utils import timezone
            fecha = timezone.now().strftime('%Y%m%d')
            ultimo_siniestro = Siniestro.objects.filter(
                numero_siniestro__startswith=f'SIN-{fecha}'
            ).count()
            self.numero_siniestro = f'SIN-{fecha}-{ultimo_siniestro + 1:03d}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Siniestro {self.numero_siniestro} - {self.vehiculo.patente}"

class FotoSiniestro(models.Model):
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='siniestros/')
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_toma = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Foto - {self.siniestro.numero_siniestro}"


class RegistroAcceso(models.Model):
    """
    Modelo para registrar entradas y salidas de vehículos al taller.
    Similar a un sistema de control de parking.
    """
    TIPO_MOVIMIENTO = (
        ('entrada', 'Entrada al Taller'),
        ('salida', 'Salida del Taller'),
    )
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='registros_acceso')
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    # Información del guardia que registra
    guardia = models.ForeignKey(
        'usuarios.Usuario', 
        on_delete=models.PROTECT,
        limit_choices_to={'rol': 'guardia'},
        related_name='registros_acceso_realizados'
    )
    
    # Información del chofer en el momento del registro
    nombre_chofer = models.CharField(max_length=100)
    telefono_chofer = models.CharField(max_length=15, blank=True)
    empresa_chofer = models.CharField(max_length=100, blank=True)
    
    # Kilometraje al momento del registro
    kilometraje = models.IntegerField(null=True, blank=True)
    
    # Observaciones y fotos
    observaciones = models.TextField(blank=True, help_text='Daños visibles, estado general, etc.')
    foto_vehiculo = models.ImageField(upload_to='acceso_vehiculos/', blank=True, null=True)
    
    # Para salidas: verificar que el vehículo esté listo
    autorizado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='salidas_autorizadas',
        help_text='Jefe de taller o mecánico que autoriza la salida'
    )
    
    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.vehiculo.patente} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def esta_en_taller(self):
        """Verifica si el vehículo está actualmente en el taller"""
        ultimo_registro = RegistroAcceso.objects.filter(
            vehiculo=self.vehiculo
        ).order_by('-fecha_hora').first()
        
        if ultimo_registro:
            return ultimo_registro.tipo_movimiento == 'entrada'
        return False