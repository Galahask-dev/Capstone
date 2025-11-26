# mantenimientos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('tareas/', views.lista_tareas, name='lista_tareas'),
    path('tareas/crear/', views.crear_tarea, name='crear_tarea'),
    
    path('tareas/<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('tareas/<int:tarea_id>/editar/', views.editar_tarea, name='editar_tarea'),
    
    # Acciones
    path('tareas/<int:tarea_id>/iniciar/', views.iniciar_tarea, name='iniciar_tarea'),
    path('tareas/<int:tarea_id>/pausar/', views.pausar_tarea, name='pausar_tarea'),
    path('tareas/<int:tarea_id>/reanudar/', views.reanudar_tarea, name='reanudar_tarea'),
    path('tareas/<int:tarea_id>/pausar-rapida/', views.pausar_rapida, name='pausar_rapida'),
    path('tareas/<int:tarea_id>/terminar-pausa/', views.terminar_pausa, name='terminar_pausa'),
    path('tareas/<int:tarea_id>/completar/', views.completar_tarea, name='completar_tarea'),
    path('tareas/<int:tarea_id>/repuestos/', views.gestionar_repuestos_tarea, name='gestionar_repuestos_tarea'),
    
    # Fotos
    path('tareas/<int:tarea_id>/fotos/subir/', views.subir_foto_tarea, name='subir_foto_tarea'),
    path('tareas/<int:tarea_id>/fotos/<int:foto_id>/eliminar/', views.eliminar_foto_tarea, name='eliminar_foto_tarea'),
]