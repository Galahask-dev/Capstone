from django.db import models

# Create your models here.
# mantenimientos/models.py
from django.db import models
from usuarios.models import Usuario
from vehiculos.models import Vehiculo

class Tarea(models.Model):
    ESTADOS_TAREA = (
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('pausada', 'Pausada'),
        ('completada', 'Completada'),
    )
    
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    )
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=20, choices=PRIORIDADES, default='media')
    estado = models.CharField(max_length=20, choices=ESTADOS_TAREA, default='pendiente')
    
    # Asignación y tiempos
    mecanico_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, limit_choices_to={'rol': 'mecanico'})
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    tiempo_estimado = models.IntegerField(help_text="Tiempo estimado en minutos", default=60)
    
    # Información adicional
    repuestos_utilizados_desc = models.TextField(blank=True, verbose_name="Repuestos Utilizados")
    observaciones_finales = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.vehiculo.patente}"

class Pausa(models.Model):
    MOTIVOS_PAUSA = (
        ('espera_repuesto', 'Espera de Repuesto'),
        ('consultas_tecnicas', 'Consultas Técnicas'),
        ('revision_supervisor', 'Revisión de Supervisor'),
        ('problema_calidad', 'Problema de Calidad'),
        ('falta_herramienta', 'Falta de Herramienta'),
        ('reunion_operativa', 'Reunión Operativa'),
        ('descanso', 'Descanso'),
        ('almuerzo', 'Almuerzo'),
        ('otro', 'Otro'),
    )
    
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='pausas')
    motivo = models.CharField(max_length=50, choices=MOTIVOS_PAUSA)
    motivo_otro = models.CharField(max_length=100, blank=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True)
    
    def duracion_minutos(self):
        if self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).total_seconds() / 60
        return None
    
    def __str__(self):
        return f"Pausa - {self.get_motivo_display()} - {self.tarea}"

class FotoTarea(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='tareas_evidencia/')
    descripcion = models.CharField(max_length=200, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Foto Tarea {self.tarea.id} - {self.fecha_subida.strftime('%d/%m/%Y')}"

class SolicitudRepuesto(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    )
    
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='solicitudes_repuestos')
    repuesto = models.ForeignKey('inventario.Repuesto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    respuesta_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_respondidas')
    
    def __str__(self):
        return f"Solicitud {self.repuesto.nombre} ({self.cantidad}) - {self.get_estado_display()}"