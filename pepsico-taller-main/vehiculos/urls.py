from django.urls import path
from . import views
from . import views_documentos  # ✅ Importamos las vistas desde el archivo correcto
from . import views_acceso  # ✅ Importar vistas de control de acceso

urlpatterns = [
    # Vistas principales
    path('', views.tablero_clinica, name='clinica_dashboard'),
    path('clinica/', views.tablero_clinica, name='tablero_clinica'),
    path('ingreso/', views.ingreso_vehiculo, name='ingreso_vehiculo'),
    path('lista/', views.lista_taller, name='lista_taller'),
    path('<int:vehiculo_id>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('<int:vehiculo_id>/editar/', views.editar_vehiculo, name='editar_vehiculo'),
    path('<int:vehiculo_id>/cambiar-estado/', views.cambiar_estado_vehiculo, name='cambiar_estado_vehiculo'),
    path('gestionar/', views.gestionar_vehiculos, name='gestionar_vehiculos'),
    path('<int:vehiculo_id>/eliminar/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('importar-excel/', views.importar_vehiculos_excel, name='importar_vehiculos_excel'),
    path('exportar-excel/', views.exportar_vehiculos_excel, name='exportar_vehiculos_excel'),
    
     # Búsqueda y tablero
    path('tablero/', views.tablero_clinica, name='tablero_clinica'),  # ← Mantener por si acaso
    path('<int:vehiculo_id>/cambiar-estado/', views.cambiar_estado_vehiculo, name='cambiar_estado_vehiculo'),

     # Documentación digital y siniestros
    path('<int:vehiculo_id>/documentos/', views_documentos.documentos_vehiculo, name='documentos_vehiculo'),
    path('<int:vehiculo_id>/documentos/subir/', views_documentos.subir_documento, name='subir_documento'),
    path('<int:vehiculo_id>/documentos/<int:documento_id>/eliminar/', views_documentos.eliminar_documento, name='eliminar_documento'),
    path('<int:vehiculo_id>/confirmar-ingreso/', views.confirmar_ingreso_vehiculo, name='confirmar_ingreso_vehiculo'),
    path('<int:vehiculo_id>/ignorar-ingreso/', views.ignorar_ingreso_vehiculo, name='ignorar_ingreso_vehiculo'),
    path('<int:vehiculo_id>/siniestros/crear/', views_documentos.crear_siniestro, name='crear_siniestro'),
    path('siniestros/', views_documentos.lista_siniestros, name='lista_siniestros'),
    path('siniestros/<int:siniestro_id>/', views_documentos.detalle_siniestro, name='detalle_siniestro'),
    path('siniestros/<int:siniestro_id>/fotos/<int:foto_id>/eliminar/', views_documentos.eliminar_foto_siniestro, name='eliminar_foto_siniestro'),
    path('ingresos/pendientes/', views.pendientes_ingreso, name='pendientes_ingreso'),
    
    # Control de Acceso Vehicular (Guardia)
    path('guardia/panel/', views_acceso.panel_guardia, name='panel_guardia'),
    path('guardia/registrar-entrada/', views_acceso.registrar_entrada, name='registrar_entrada'),
    path('guardia/registrar-salida/<int:vehiculo_id>/', views_acceso.registrar_salida, name='registrar_salida'),
    path('guardia/historial/', views_acceso.historial_acceso, name='historial_acceso'),
    path('guardia/registro/<int:registro_id>/', views_acceso.detalle_registro, name='detalle_registro'),
    
    # Debug (solo para administradores)
    path('debug/archivos/', views_documentos.debug_archivos, name='debug_archivos'),
]


  