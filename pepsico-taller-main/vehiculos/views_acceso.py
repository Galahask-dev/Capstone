# vehiculos/views_acceso.py
"""
Vistas para el sistema de control de acceso vehicular (Guardia)
Similar a un sistema de parking que registra entradas y salidas
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Vehiculo, RegistroAcceso
from .forms import RegistroEntradaForm, RegistroSalidaForm


@login_required
def panel_guardia(request):
    """
    Panel principal del guardia con resumen de vehículos en taller
    """
    if request.user.rol not in ['guardia', 'admin', 'jefe_taller']:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('/')
    
    # Obtener vehículos actualmente en el taller
    vehiculos_en_taller = []
    for vehiculo in Vehiculo.objects.filter(activo=True):
        ultimo_registro = RegistroAcceso.objects.filter(
            vehiculo=vehiculo
        ).order_by('-fecha_hora').first()
        en_taller_por_registro = ultimo_registro and ultimo_registro.tipo_movimiento == 'entrada'
        en_taller_por_estado = vehiculo.estado in ['ingresado', 'diagnostico', 'reparacion', 'listo']
        if en_taller_por_registro or en_taller_por_estado:
            vehiculos_en_taller.append({
                'vehiculo': vehiculo,
                'registro_entrada': ultimo_registro if en_taller_por_registro else None,
                'puede_salir': vehiculo.estado in ['listo', 'entregado']
            })
    
    # Vehículos listos para salir
    vehiculos_listos = Vehiculo.objects.filter(
        estado__in=['listo', 'entregado'],
        activo=True
    )
    
    # Últimos registros de acceso
    ultimos_registros = RegistroAcceso.objects.select_related(
        'vehiculo', 'guardia'
    ).order_by('-fecha_hora')[:10]
    
    # Estadísticas del día (rango horario local)
    hoy_local = timezone.localdate()
    from datetime import datetime, time
    inicio_hoy = timezone.make_aware(datetime.combine(hoy_local, time.min))
    fin_hoy = timezone.make_aware(datetime.combine(hoy_local, time.max))
    entradas_hoy = RegistroAcceso.objects.filter(
        fecha_hora__gte=inicio_hoy,
        fecha_hora__lte=fin_hoy,
        tipo_movimiento='entrada'
    ).count()
    salidas_hoy = RegistroAcceso.objects.filter(
        fecha_hora__gte=inicio_hoy,
        fecha_hora__lte=fin_hoy,
        tipo_movimiento='salida'
    ).count()
    
    context = {
        'vehiculos_en_taller': vehiculos_en_taller,
        'total_en_taller': len(vehiculos_en_taller),
        'vehiculos_listos': vehiculos_listos,
        'ultimos_registros': ultimos_registros,
        'entradas_hoy': entradas_hoy,
        'salidas_hoy': salidas_hoy,
    }
    
    return render(request, 'vehiculos/guardia/panel_guardia.html', context)


@login_required
def registrar_entrada(request):
    """
    Registrar la entrada de un vehículo al taller
    """
    if request.user.rol not in ['guardia', 'admin']:
        messages.error(request, 'No tienes permisos para registrar entradas.')
        return redirect('panel_guardia')
    
    vehiculo = None
    patente_buscada = request.GET.get('patente', '').upper()
    
    # Si se proporciona una patente en GET, buscar el vehículo
    if patente_buscada:
        try:
            vehiculo = Vehiculo.objects.get(patente=patente_buscada)
            
            # Verificar si ya está en el taller
            ultimo_registro = RegistroAcceso.objects.filter(
                vehiculo=vehiculo
            ).order_by('-fecha_hora').first()
            
            if ultimo_registro and ultimo_registro.tipo_movimiento == 'entrada':
                messages.warning(
                    request, 
                    f'El vehículo {patente_buscada} ya se encuentra en el taller desde {ultimo_registro.fecha_hora.strftime("%d/%m/%Y %H:%M")}'
                )
                return redirect('panel_guardia')
                
        except Vehiculo.DoesNotExist:
            messages.error(
                request,
                f'El vehículo con patente {patente_buscada} no está registrado en el sistema. Por favor, regístralo primero.'
            )
            return redirect('ingreso_vehiculo')
    
    if request.method == 'POST':
        form = RegistroEntradaForm(request.POST, request.FILES)
        
        if form.is_valid():
            patente = form.cleaned_data['patente'].upper()
            
            # Buscar el vehículo
            try:
                vehiculo = Vehiculo.objects.get(patente=patente)
                
                # Verificar si ya está en el taller
                ultimo_registro = RegistroAcceso.objects.filter(
                    vehiculo=vehiculo
                ).order_by('-fecha_hora').first()
                
                if ultimo_registro and ultimo_registro.tipo_movimiento == 'entrada':
                    messages.warning(
                        request, 
                        f'El vehículo {patente} ya se encuentra en el taller desde {ultimo_registro.fecha_hora.strftime("%d/%m/%Y %H:%M")}'
                    )
                    return redirect('panel_guardia')
                
            except Vehiculo.DoesNotExist:
                vehiculo = Vehiculo(
                    patente=patente,
                    tipo_vehiculo='automovil',
                    marca='Desconocido',
                    modelo='Desconocido',
                    año=timezone.now().year,
                    numero_chasis='',
                    kilometraje=0,
                    activo=True,
                    nombre_chofer='',
                    telefono_chofer='',
                    empresa_chofer='',
                    estado='ingresado',
                    motivo_ingreso='Ingreso rápido por guardia',
                    observaciones_ingreso='',
                    guardia_ingreso=request.user,
                )
                vehiculo.save()
            
            # Crear el registro de entrada (usar kilometraje del vehículo)
            registro = RegistroAcceso(
                vehiculo=vehiculo,
                tipo_movimiento='entrada',
                guardia=request.user,
                nombre_chofer=getattr(vehiculo, 'nombre_chofer', '') or '',
                telefono_chofer='',
                empresa_chofer='',
                kilometraje=vehiculo.kilometraje,
                observaciones=form.cleaned_data.get('observaciones', ''),
            )
            
            if 'foto_vehiculo' in request.FILES:
                registro.foto_vehiculo = request.FILES['foto_vehiculo']
            
            registro.save()
            
            # Actualizar el estado del vehículo si estaba entregado
            if vehiculo.estado == 'entregado':
                vehiculo.estado = 'ingresado'
                vehiculo.save()
            
            messages.success(
                request,
                f'✅ Entrada registrada correctamente para {vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}'
            )
            return redirect('panel_guardia')
    else:
        # Pre-llenar el formulario con datos del vehículo si existe
        initial_data = {}
        if vehiculo:
            initial_data = {
                'patente': vehiculo.patente,
            }
        elif patente_buscada:
            initial_data['patente'] = patente_buscada
            
        form = RegistroEntradaForm(initial=initial_data)
    
    context = {
        'form': form,
        'vehiculo': vehiculo,
        'titulo': 'Registrar Entrada de Vehículo'
    }
    
    return render(request, 'vehiculos/guardia/registrar_entrada.html', context)



@login_required
def registrar_salida(request, vehiculo_id):
    """
    Registrar la salida de un vehículo del taller
    """
    if request.user.rol not in ['guardia', 'admin']:
        messages.error(request, 'No tienes permisos para registrar salidas.')
        return redirect('dashboard_guardia')
    
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    # Verificar que el vehículo esté en el taller
    ultimo_registro = RegistroAcceso.objects.filter(
        vehiculo=vehiculo
    ).order_by('-fecha_hora').first()
    
    # Verificar si está en el taller (por registro o por estado)
    esta_en_taller = (ultimo_registro and ultimo_registro.tipo_movimiento == 'entrada') or \
                     (vehiculo.estado in ['ingresado', 'diagnostico', 'reparacion', 'listo'])
    
    if not esta_en_taller:
        messages.error(request, f'El vehículo {vehiculo.patente} no se encuentra actualmente en el taller (según registros).')
        return redirect('dashboard_guardia')
    
    # Solo mostrar advertencia informativa si no está listo (no bloquear la salida)
    advertencia = None
    if vehiculo.estado not in ['listo', 'entregado']:
        advertencia = f'Nota: El vehículo está en estado "{vehiculo.get_estado_display()}". Asegúrese de que esté autorizado para salir.'
    
    if request.method == 'POST':
        form = RegistroSalidaForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Crear el registro de salida
            registro = RegistroAcceso(
                vehiculo=vehiculo,
                tipo_movimiento='salida',
                guardia=request.user,
                nombre_chofer=form.cleaned_data['nombre_chofer'],
                telefono_chofer=form.cleaned_data.get('telefono_chofer', ''),
                kilometraje=form.cleaned_data.get('kilometraje'),
                observaciones=form.cleaned_data.get('observaciones', ''),
            )
            
            if 'foto_vehiculo' in request.FILES:
                registro.foto_vehiculo = request.FILES['foto_vehiculo']
            
            registro.save()
            
            # Actualizar el estado del vehículo
            vehiculo.estado = 'entregado'
            vehiculo.fecha_salida = timezone.now()
            vehiculo.save()
            
            messages.success(
                request,
                f'✅ Salida registrada correctamente para {vehiculo.patente} - {vehiculo.marca} {vehiculo.modelo}'
            )
            return redirect('dashboard_guardia')
    else:
        # Pre-llenar con datos del vehículo
        form = RegistroSalidaForm(initial={
            'nombre_chofer': vehiculo.nombre_chofer,
            'telefono_chofer': vehiculo.telefono_chofer,
        })
    
    context = {
        'form': form,
        'vehiculo': vehiculo,
        'registro_entrada': ultimo_registro,
        'advertencia': advertencia,
        'titulo': f'Registrar Salida - {vehiculo.patente}'
    }
    
    return render(request, 'vehiculos/guardia/registrar_salida.html', context)


@login_required
def historial_acceso(request):
    """
    Historial completo de entradas y salidas
    """
    if request.user.rol not in ['guardia', 'admin', 'jefe_taller']:
        messages.error(request, 'No tienes permisos para ver el historial.')
        return redirect('/')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    patente = request.GET.get('patente')
    tipo_movimiento = request.GET.get('tipo_movimiento')
    
    registros = RegistroAcceso.objects.select_related(
        'vehiculo', 'guardia'
    ).order_by('-fecha_hora')
    
    # Aplicar filtros
    if fecha_desde:
        registros = registros.filter(fecha_hora__date__gte=fecha_desde)
    
    if fecha_hasta:
        registros = registros.filter(fecha_hora__date__lte=fecha_hasta)
    
    if patente:
        registros = registros.filter(vehiculo__patente__icontains=patente)
    
    if tipo_movimiento:
        registros = registros.filter(tipo_movimiento=tipo_movimiento)
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(registros, 25)  # 25 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'patente': patente,
        'tipo_movimiento': tipo_movimiento,
    }
    
    return render(request, 'vehiculos/guardia/historial_acceso.html', context)


@login_required
def detalle_registro(request, registro_id):
    """
    Ver detalles de un registro de acceso específico
    """
    if request.user.rol not in ['guardia', 'admin', 'jefe_taller']:
        messages.error(request, 'No tienes permisos para ver este registro.')
        return redirect('/')
    
    registro = get_object_or_404(
        RegistroAcceso.objects.select_related('vehiculo', 'guardia', 'autorizado_por'),
        id=registro_id
    )
    
    context = {
        'registro': registro,
    }
    
    return render(request, 'vehiculos/guardia/detalle_registro.html', context)
