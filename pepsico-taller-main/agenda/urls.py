# agenda/urls.py
from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('lista/', views.lista_citas, name='lista_citas'),
    path('detalle/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('cancelar/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'), 
    path('disponibilidad/', views.disponibilidad_dia, name='disponibilidad_dia'),
]
