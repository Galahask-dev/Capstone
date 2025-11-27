# vehiculos/views_documentos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Vehiculo, DocumentoVehiculo, Siniestro, FotoSiniestro
from .forms_documentos import DocumentoVehiculoForm, SiniestroForm, FotoSiniestroForm

@login_required
def documentos_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    documentos = vehiculo.documentos.all().order_by('-fecha_subida')
    
    # Documentos vencidos o próximos a vencer
    from django.utils import timezone
    from datetime import timedelta
    hoy = timezone.now().date()
    treinta_dias = hoy + timedelta(days=30)
    
    documentos_vencidos = documentos.filter(fecha_vencimiento__lt=hoy)
    documentos_proximos_vencer = documentos.filter(
        fecha_vencimiento__gte=hoy, 
        fecha_vencimiento__lte=treinta_dias
    )
    
    context = {
        'vehiculo': vehiculo,
        'documentos': documentos,
        'documentos_vencidos': documentos_vencidos,
        'documentos_proximos_vencer': documentos_proximos_vencer,
    }
    return render(request, 'vehiculos/documentos_vehiculo.html', context)

@login_required
def subir_documento(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        form = DocumentoVehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.vehiculo = vehiculo
            documento.subido_por = request.user
            
            # Verificar que el archivo se haya subido correctamente
            if documento.archivo:
                try:
                    documento.save()
                    # Verificar que el archivo existe después de guardar
                    if documento.archivo and hasattr(documento.archivo, 'path'):
                        import os
                        if os.path.exists(documento.archivo.path):
                            messages.success(request, 
                                f'✅ Documento {documento.get_tipo_documento_display()} subido exitosamente! '
                                f'Archivo: {documento.nombre_archivo}')
                        else:
                            messages.error(request, 
                                '❌ Error: El archivo se guardó en la base de datos pero no se encuentra en el disco.')
                    else:
                        messages.warning(request, 
                            '⚠️ El documento se guardó pero hay problemas de acceso al archivo.')
                    
                    return redirect('documentos_vehiculo', vehiculo_id=vehiculo.id)
                except Exception as e:
                    messages.error(request, f'❌ Error al guardar el documento: {str(e)}')
            else:
                messages.error(request, '❌ No se seleccionó ningún archivo.')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    else:
        form = DocumentoVehiculoForm()
    
    context = {
        'vehiculo': vehiculo,
        'form': form,
    }
    return render(request, 'vehiculos/subir_documento.html', context)

@login_required
def crear_siniestro(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        form = SiniestroForm(request.POST)
        if form.is_valid():
            siniestro = form.save(commit=False)
            siniestro.vehiculo = vehiculo
            siniestro.reportado_por = request.user
            
            # Generar número de siniestro automático
            from django.utils import timezone
            fecha = timezone.now().strftime('%Y%m%d')
            ultimo_siniestro = Siniestro.objects.filter(
                numero_siniestro__startswith=f'SIN-{fecha}'
            ).count()
            siniestro.numero_siniestro = f'SIN-{fecha}-{ultimo_siniestro + 1:03d}'
            
            siniestro.save()
            
            messages.success(request, f'Siniestro {siniestro.numero_siniestro} creado exitosamente!')
            return redirect('detalle_siniestro', siniestro_id=siniestro.id)
    else:
        form = SiniestroForm()
    
    context = {
        'vehiculo': vehiculo,
        'form': form,
    }
    return render(request, 'vehiculos/crear_siniestro.html', context)

@login_required
def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    fotos = siniestro.fotos.all()
    
    if request.method == 'POST':
        form_foto = FotoSiniestroForm(request.POST, request.FILES)
        if form_foto.is_valid():
            foto = form_foto.save(commit=False)
            foto.siniestro = siniestro
            foto.save()
            messages.success(request, 'Foto agregada al siniestro!')
            return redirect('detalle_siniestro', siniestro_id=siniestro.id)
        else:
            messages.error(request, 'Error al subir la foto. Verifica el archivo y los campos.')
    else:
        form_foto = FotoSiniestroForm()
    
    context = {
        'siniestro': siniestro,
        'fotos': fotos,
        'form_foto': form_foto,
    }
    return render(request, 'vehiculos/detalle_siniestro.html', context)

@login_required
def lista_siniestros(request):
    siniestros = Siniestro.objects.select_related('vehiculo', 'reportado_por').all()
    
    estado = request.GET.get('estado')
    if estado:
        siniestros = siniestros.filter(estado=estado)
    
    context = {
        'siniestros': siniestros,
        'filtro_estado': estado,
    }
    return render(request, 'vehiculos/lista_siniestros.html', context)

@login_required
def eliminar_foto_siniestro(request, siniestro_id, foto_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    foto = get_object_or_404(FotoSiniestro, id=foto_id, siniestro=siniestro)

    if not (request.user.is_superuser or request.user.rol in ['admin', 'jefe_taller', 'ehs'] or request.user == siniestro.reportado_por):
        messages.error(request, 'No tienes permisos para eliminar fotografías.')
        return redirect('detalle_siniestro', siniestro_id=siniestro.id)

    if request.method == 'POST':
        try:
            imagen_path = foto.imagen.path if foto.imagen and hasattr(foto.imagen, 'path') else None
            if imagen_path:
                import os
                if os.path.exists(imagen_path):
                    try:
                        os.remove(imagen_path)
                    except OSError as e:
                        messages.warning(request, f'Error al eliminar el archivo físico: {str(e)}')
            foto.delete()
            messages.success(request, 'Fotografía eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la fotografía: {str(e)}')
    else:
        messages.error(request, 'Método no válido para eliminar fotografía.')

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)

@login_required
def eliminar_documento(request, vehiculo_id, documento_id):
    """Vista para eliminar un documento"""
    print(f"🔍 DEBUG: Eliminando documento ID {documento_id} del vehículo ID {vehiculo_id}")
    print(f"👤 Usuario autenticado: {request.user.is_authenticated}")
    
    if not request.user.is_authenticated:
        print("❌ Usuario no autenticado, redirigiendo a login")
        messages.error(request, 'Debes iniciar sesión para eliminar documentos.')
        return redirect('login')
    
    print(f"👤 Usuario: {request.user.username} ({getattr(request.user, 'rol', 'sin_rol')})")
    
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    documento = get_object_or_404(DocumentoVehiculo, id=documento_id, vehiculo=vehiculo)
    
    print(f"📄 Documento encontrado: {documento.get_tipo_documento_display()} - {documento.nombre_archivo}")
    
    # Verificar permisos
    if not (request.user.is_superuser or request.user.rol in ['admin', 'jefe_taller']):
        print(f"❌ Sin permisos: {request.user.rol}")
        messages.error(request, 'No tienes permisos para eliminar documentos.')
        return redirect('documentos_vehiculo', vehiculo_id=vehiculo.id)
    
    if request.method == 'POST':
        print("📝 Método POST recibido para eliminación")
        try:
            # Guardar información del documento antes de eliminarlo
            tipo_documento = documento.get_tipo_documento_display()
            nombre_archivo = documento.nombre_archivo or documento.archivo.name
            archivo_path = documento.archivo.path if documento.archivo else None
            
            print(f"📂 Archivo a eliminar: {archivo_path}")
            
            # Eliminar el archivo físico del disco
            if documento.archivo:
                import os
                if hasattr(documento.archivo, 'path') and os.path.exists(documento.archivo.path):
                    try:
                        os.remove(documento.archivo.path)
                        print(f"🗑️ Archivo físico eliminado: {documento.archivo.path}")
                    except OSError as e:
                        print(f"⚠️ Error eliminando archivo físico: {str(e)}")
                        messages.warning(request, f'Archivo eliminado de la base de datos pero no del disco: {str(e)}')
            
            # Eliminar el registro de la base de datos
            documento.delete()
            print(f"🗄️ Registro de base de datos eliminado")
            
            messages.success(request, f'✅ Documento "{tipo_documento}" ({nombre_archivo}) eliminado exitosamente.')
            
        except Exception as e:
            print(f"❌ Error en eliminación: {str(e)}")
            messages.error(request, f'❌ Error al eliminar el documento: {str(e)}')
    else:
        print("❓ Método no es POST")
        messages.error(request, 'Método no válido para eliminar documento.')
    
    return redirect('documentos_vehiculo', vehiculo_id=vehiculo.id)

@login_required  
def debug_archivos(request):
    """Vista de debug para verificar el estado de los archivos"""
    if not (request.user.is_superuser or request.user.rol == 'admin'):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('clinica_dashboard')
    
    import os
    from django.conf import settings
    
    documentos = DocumentoVehiculo.objects.all().order_by('-fecha_subida')[:20]  # Últimos 20
    
    debug_info = []
    for doc in documentos:
        info = {
            'documento': doc,
            'archivo_url': doc.archivo.url if doc.archivo else 'Sin archivo',
            'archivo_path': doc.archivo.path if doc.archivo else 'Sin path',
            'archivo_existe': os.path.exists(doc.archivo.path) if doc.archivo else False,
            'archivo_size': doc.archivo.size if doc.archivo else 0,
        }
        debug_info.append(info)
    
    # Información del directorio media
    media_root = settings.MEDIA_ROOT
    documentos_dir = os.path.join(media_root, 'documentos_vehiculos')
    
    context = {
        'debug_info': debug_info,
        'media_root': media_root,
        'documentos_dir': documentos_dir,
        'documentos_dir_existe': os.path.exists(documentos_dir),
        'archivos_en_dir': os.listdir(documentos_dir) if os.path.exists(documentos_dir) else [],
    }
    
    return render(request, 'vehiculos/debug_archivos.html', context)