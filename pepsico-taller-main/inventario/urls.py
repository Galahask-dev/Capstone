# inventario/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_inventario, name='dashboard_inventario'),
    path('repuestos/', views.lista_repuestos, name='lista_repuestos'),
    path('repuestos/crear/', views.crear_repuesto, name='crear_repuesto'),
    path('repuestos/<int:repuesto_id>/', views.detalle_repuesto, name='detalle_repuesto'),
    path('repuestos/<int:repuesto_id>/editar/', views.editar_repuesto, name='editar_repuesto'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    
    path('movimientos/entrada/', views.movimiento_entrada, name='movimiento_entrada'),
    path('movimientos/salida/', views.movimiento_salida, name='movimiento_salida'),
    path('ajustes/crear/', views.crear_ajuste, name='crear_ajuste'),
    
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/<int:pedido_id>/recibir/', views.recibir_pedido, name='recibir_pedido'),
    
    # Bodeguero Flow
    path('solicitudes/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('solicitudes/<int:solicitud_id>/aprobar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<int:solicitud_id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
]