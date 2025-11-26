"""
URL configuration for pepsico_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# pepsico_project/urls.py - VERIFICAR QUE ESTÉ INCLUIDA
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from vehiculos.views import busqueda_avanzada 
from usuarios.views import custom_login, custom_logout  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('vehiculos.urls')),
    path('login/', custom_login, name='login'),  # ← Esta línea debe estar
    path('logout/', custom_logout, name='logout'),  # ← Y esta también
    path('usuarios/', include('usuarios.urls')),
    path('vehiculos/', include('vehiculos.urls')),
    path('mantenimientos/', include('mantenimientos.urls')),
    path('reportes/', include('reportes.urls')),
    path('inventario/', include('inventario.urls')),
    path('buscar/', busqueda_avanzada, name='busqueda_avanzada'),
    path('agenda/', include('agenda.urls')),  # ← AGREGAR ESTA LÍNEA
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

