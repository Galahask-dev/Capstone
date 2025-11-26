# usuarios/models.py - MODIFICAR ROLES
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('jefe_taller', 'Jefe de Taller'),
        ('mecanico', 'Mecánico'),
        ('chofer', 'Chofer'),
        ('vendedor', 'Vendedor/Preventista'), 
        ('guardia', 'Guardia'),
        ('bodeguero', 'Bodeguero'),
        ('ehs', 'EHS'),
        ('recepcionista', 'Recepcionista de Vehículos'),
    )
    
    rol = models.CharField(max_length=30, choices=ROLES, default='mecanico')
    telefono = models.CharField(max_length=15, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    foto = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    especialidad = models.CharField(max_length=100, blank=True)
    turno = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"