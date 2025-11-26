# reportes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_reportes, name='dashboard_reportes'),
    path('productividad/', views.reporte_productividad, name='reporte_productividad'),
    path('productividad/<int:mecanico_id>/', views.reporte_productividad_detalle, name='reporte_productividad_detalle'),
    path('tiempos-pausas/', views.reporte_tiempos_pausas, name='reporte_tiempos_pausas'),
    path('tiempos-taller/', views.reporte_tiempos_taller, name='reporte_tiempos_taller'),  # ← AGREGAR
]