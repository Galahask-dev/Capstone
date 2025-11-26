# usuarios/urls.py 
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'), 
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/exportar-excel/', views.exportar_usuarios_excel, name='exportar_usuarios_excel'),
    path('usuarios/importar/', views.importar_usuarios, name='importar_usuarios'),
    path('usuarios/importar-excel/', views.importar_usuarios_excel, name='importar_usuarios_excel'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    # View-as-role: permitir a administradores ver la aplicación como otro rol
    path('role-selector/', views.role_selector, name='role_selector'),
    path('clear-view-as-role/', views.clear_view_as_role, name='clear_view_as_role'),
    # Dashboards específicos por rol
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/mecanico/', views.dashboard_mecanico, name='dashboard_mecanico'),
    path('dashboard/chofer/', views.dashboard_chofer, name='dashboard_chofer'),
    path('dashboard/guardia/', views.dashboard_guardia, name='dashboard_guardia'),
    path('dashboard/ehs/', views.dashboard_ehs, name='dashboard_ehs'),
    path('dashboard/vendedor/', views.dashboard_vendedor, name='dashboard_vendedor'),
    path('dashboard/bodeguero/', views.dashboard_bodeguero, name='dashboard_bodeguero'),
    path('dashboard/jefe-taller/', views.dashboard_jefe_taller, name='dashboard_jefe_taller'),
    path('dashboard/recepcionista/', views.dashboard_recepcionista, name='dashboard_recepcionista'),
    path('tarea/<int:tarea_id>/asignar/', views.asignar_tarea, name='asignar_tarea'),
]
