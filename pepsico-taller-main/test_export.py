#!/usr/bin/env python
"""
Script de prueba para verificar que la función de exportar usuarios funciona correctamente.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pepsico_project.settings')
django.setup()

from usuarios.views import exportar_usuarios_excel
from django.test import RequestFactory
from usuarios.models import Usuario
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage

def test_export_function():
    """Prueba básica de la función de exportar usuarios"""
    print("🧪 Iniciando prueba de exportar usuarios...")
    
    # Crear un request factory
    factory = RequestFactory()
    
    # Crear un usuario administrador de prueba
    try:
        admin_user = Usuario.objects.get(username='admin')
        print(f"✅ Usuario admin encontrado: {admin_user}")
    except Usuario.DoesNotExist:
        print("⚠️  No se encontró usuario admin, creando uno...")
        admin_user = Usuario.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123',
            rol='admin'
        )
        print(f"✅ Usuario admin creado: {admin_user}")
    
    # Crear una request simulada
    request = factory.get('/usuarios/exportar-excel/')
    request.user = admin_user
    
    # Agregar soporte para mensajes
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    try:
        print("🔄 Ejecutando función exportar_usuarios_excel...")
        response = exportar_usuarios_excel(request)
        
        if hasattr(response, 'status_code') and response.status_code == 200:
            print("✅ Función ejecutada exitosamente!")
            print(f"   - Tipo de respuesta: {type(response)}")
            print(f"   - Content-Type: {response.get('Content-Type', 'No definido')}")
            print(f"   - Content-Disposition: {response.get('Content-Disposition', 'No definido')}")
            return True
        else:
            print(f"❌ Error: Respuesta inesperada: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error al ejecutar la función: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_export_function()
    if success:
        print("\n🎉 ¡Prueba exitosa! La función de exportar usuarios funciona correctamente.")
    else:
        print("\n💥 La prueba falló. Revisa los errores anteriores.")