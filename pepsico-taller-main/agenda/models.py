

# Create your models here.
# agenda/models.py
from django.db import models
from vehiculos.models import Vehiculo
from usuarios.models import Usuario

class CitaMantenimiento(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    )
    
    TIPO_MANTENCION_CHOICES = (
        ('preventiva', 'Mantención Preventiva'),
        ('correctiva', 'Reparación Correctiva'),
        ('neumaticos', 'Cambio de Neumáticos'),
        ('dpf', 'Limpieza DPF'),
        ('bateria', 'Reemplazo de Batería'),
        ('otro', 'Otro'),
    )

    # Campo de texto para la patente (obligatorio)
    patente = models.CharField(max_length=10, help_text="Patente del vehículo (ej. ABC123)")
    
    # Campo opcional para vincular al Vehiculo cuando exista
    vehiculo = models.ForeignKey(
        'vehiculos.Vehiculo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citas'
    )

    solicitante = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas_solicitadas')
    fecha_hora = models.DateTimeField(help_text="Fecha y hora de la cita")
    duracion_minutos = models.PositiveIntegerField(default=60, help_text="Duración estimada en minutos")
    tipo_mantencion = models.CharField(max_length=20, choices=TIPO_MANTENCION_CHOICES, default='preventiva')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cita de Mantenimiento"
        verbose_name_plural = "Citas de Mantenimiento"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"Cita {self.get_tipo_mantencion_display()} - {self.patente} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Intentar vincular automáticamente con vehículo si no está vinculado
        if not self.vehiculo:
            try:
                # Intentar obtener un vehículo que tenga la misma patente
                vehiculo = Vehiculo.objects.get(patente=self.patente)
                self.vehiculo = vehiculo
            except Vehiculo.DoesNotExist:
                pass  # Mantener vehiculo como None si no se encuentra

        # Guardar la cita de mantenimiento
        super().save(*args, **kwargs)
