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
    path('eliminar/<int:cita_id>/', views.eliminar_cita, name='eliminar_cita'),
    path('aceptar/<int:cita_id>/', views.aceptar_cita, name='aceptar_cita'),
    path('completar/patente/<str:patente>/', views.completar_cita_patente, name='completar_cita_patente'),
]
