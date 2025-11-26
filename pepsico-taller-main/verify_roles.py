#!/usr/bin/env python
"""
Script de verificación para las nuevas funcionalidades de roles.
"""
import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pepsico_project.settings')
django.setup()
settings.ALLOWED_HOSTS += ['testserver']

from django.test import RequestFactory, Client
from django.urls import reverse
from usuarios.models import Usuario
from vehiculos.models import Vehiculo
from mantenimientos.models import Tarea, FotoTarea
from django.core.files.uploadedfile import SimpleUploadedFile

def verify_features():
    print("Iniciando verificacion de funcionalidades...")
    
    # 1. Setup Data
    try:
        mecanico = Usuario.objects.get(username='mecanico_test')
    except Usuario.DoesNotExist:
        mecanico = Usuario.objects.create_user(username='mecanico_test', password='password', rol='mecanico')
        
    try:
        chofer = Usuario.objects.get(username='chofer_test')
    except Usuario.DoesNotExist:
        chofer = Usuario.objects.create_user(username='chofer_test', password='password', rol='chofer')

    try:
        vehiculo = Vehiculo.objects.get(patente='TEST-001')
    except Vehiculo.DoesNotExist:
        vehiculo = Vehiculo.objects.create(patente='TEST-001', marca='Test', modelo='Test', año=2023, tipo_vehiculo='camion')

    tarea = Tarea.objects.create(
        vehiculo=vehiculo,
        titulo='Tarea de Prueba',
        descripcion='Prueba de fotos',
        mecanico_asignado=mecanico,
        estado='en_proceso'
    )
    
    print("Datos de prueba creados.")

    # 2. Verify FotoTarea Model
    print("\nVerificando modelo FotoTarea...")
    foto = FotoTarea.objects.create(
        tarea=tarea,
        imagen=SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg"),
        descripcion="Foto de prueba",
        subido_por=mecanico
    )
    if foto.pk:
        print(f"FotoTarea creada exitosamente: {foto}")
    else:
        print("Error al crear FotoTarea")

    # 3. Verify Chofer Dashboard Links
    print("\nVerificando Dashboard Chofer...")
    client = Client()
    client.force_login(chofer)
    response = client.get(reverse('dashboard_chofer'))
    
    content = response.content.decode('utf-8')
    # Check for the text label or the rendered URL part
    if 'Agendar Cita' in content and 'Mis Citas' in content:
        print("Enlaces de Agenda encontrados en el dashboard.")
    else:
        print("Faltan enlaces de Agenda en el dashboard.")
        print("Contenido parcial (body):", content[content.find('<body'):content.find('<body')+1000])

    # 4. Verify Mechanic Photo Upload View
    print("\nVerificando Vista Subida Foto Mecanico...")
    client.force_login(mecanico)
    
    # Small valid GIF
    gif_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    
    with open('test_upload.gif', 'wb') as f:
        f.write(gif_content)
        
    with open('test_upload.gif', 'rb') as f:
        response = client.post(
            reverse('subir_foto_tarea', args=[tarea.id]),
            {'imagen': f, 'descripcion': 'Subida desde vista'},
            follow=True
        )
    
    if response.status_code == 200:
        print("Vista de subida respondio 200 OK (tras redirect).")
        
        # Check messages in HTML content since context might be tricky in script
        response_html = response.content.decode('utf-8')
        if 'Foto subida exitosamente' in response_html:
            print("Mensaje de exito encontrado en HTML.")
        elif 'Error al subir la foto' in response_html:
            print("Mensaje de error encontrado en HTML.")
        else:
            print("No se encontraron mensajes especificos en HTML.")

        # Verificar que se creó la foto
        if FotoTarea.objects.filter(descripcion='Subida desde vista').exists():
             print("Foto creada en BD via vista.")
        else:
             print("Foto NO creada en BD via vista.")
             # Print form errors if possible (not easy without context)
             # But we can check if the file was actually sent
             print(f"Archivos enviados: {len(response.request.get('FILES', [])) if hasattr(response, 'request') else 'Unknown'}")
    else:
        print(f"Error en vista de subida: {response.status_code}")

    # Cleanup
    if os.path.exists('test_upload.gif'):
        os.remove('test_upload.gif')
    print("\nVerificacion completada.")

if __name__ == "__main__":
    verify_features()
