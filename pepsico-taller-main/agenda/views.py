# agenda/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models  # Importante para F y Q
from .models import CitaMantenimiento
from .forms import CitaMantenimientoForm
from vehiculos.models import Vehiculo
from datetime import timedelta, datetime, time
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q # Importar Q si no está


@login_required
def agendar_cita(request):
    # Permitir a vendedores agendar citas
    if request.user.rol not in ['chofer', 'vendedor', 'jefe_taller', 'admin']:
        messages.error(request, 'No tienes permiso para agendar citas.')
        return redirect('clinica_dashboard')

    if request.method == 'POST':
        form = CitaMantenimientoForm(request.POST, user=request.user)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.solicitante = request.user

            # Calcular rangos de tiempo
            inicio_cita = cita.fecha_hora
            fin_cita = cita.fecha_hora + timedelta(minutes=cita.duracion_minutos)

            # Buscar CITAS ACTIVAS potencialmente solapadas (mismo día)
            # Luego verificar solapamiento en Python para compatibilidad con SQLite
            posibles = CitaMantenimiento.objects.filter(
                patente=cita.patente,
                estado__in=['pendiente', 'confirmada'],
                fecha_hora__date=inicio_cita.date()
            )

            solapamientos = []
            for c in posibles:
                c_inicio = c.fecha_hora
                c_fin = c_inicio + timedelta(minutes=c.duracion_minutos)
                if inicio_cita < c_fin and c_inicio < fin_cita:
                    solapamientos.append(c)

            if solapamientos:
                cita_existente = solapamientos[0]
                # Asumiendo que timezone.now() es el timezone local correcto o se convierte
                # from django.utils import timezone
                # fecha_hora_formateada = cita_existente.fecha_hora.astimezone(timezone.get_current_timezone())
                # Usamos el objeto datetime directamente si está en el tz correcto
                fecha_hora_formateada = cita_existente.fecha_hora

                messages.error(
                    request,
                    f'❌ CONFLICTO: Ya existe una cita para {cita.patente} '
                    f'programada el {fecha_hora_formateada.strftime("%d/%m/%Y a las %H:%M")}. '
                    f'Por favor, elige un horario diferente.'
                )
                return render(request, 'agenda/agendar_cita.html', {'form': form})
            else:
                cita.save()
                messages.success(
                    request,
                    f'✅ Cita agendada exitosamente para {cita.patente} '
                    f'el {cita.fecha_hora.strftime("%d/%m/%Y a las %H:%M")}'
                )
                # Redirigir según rol
                if request.user.rol == 'vendedor':
                    return redirect('dashboard_vendedor') # Asegúrate que esta URL existe
                elif request.user.rol == 'chofer':
                    return redirect('agenda:mis_citas')
                else:
                    return redirect('agenda:lista_citas')
    else:
        form = CitaMantenimientoForm(user=request.user)

    return render(request, 'agenda/agendar_cita.html', {'form': form})

def _generate_hourly_slots():
    slots = []
    h = 8
    m = 30
    while True:
        t = time(hour=h, minute=m)
        slots.append(t)
        if h == 18 and m == 30:
            break
        h = h + 1
        if h == 24:
            break
    return slots

@login_required
def disponibilidad_dia(request):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'date requerido'}, status=400)
    try:
        day = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'formato de fecha inválido'}, status=400)

    now = timezone.localtime()
    citas = CitaMantenimiento.objects.filter(
        fecha_hora__date=day,
        estado__in=['pendiente', 'confirmada']
    ).only('id', 'fecha_hora', 'duracion_minutos', 'estado')

    ocupados = []
    for c in citas:
        inicio = timezone.localtime(c.fecha_hora)
        fin = inicio + timedelta(minutes=c.duracion_minutos)
        ocupados.append((inicio, fin, c))

    slot_length = timedelta(minutes=60)
    slots = []
    for t in _generate_hourly_slots():
        inicio_slot = timezone.make_aware(datetime.combine(day, t), timezone.get_current_timezone())
        fin_slot = inicio_slot + slot_length
        estado = 'disponible'
        cita_info = None
        for (ini, fin, c) in ocupados:
            if inicio_slot < fin and ini < fin_slot:
                estado = 'ocupado'
                cita_info = {
                    'id': c.id,
                    'estado': c.estado,
                    'duracion_minutos': c.duracion_minutos,
                }
                break
        slots.append({
            'time': t.strftime('%H:%M'),
            'estado': estado,
            'cita': cita_info,
            'is_past': inicio_slot < now,
        })

    return JsonResponse({
        'date': day.strftime('%Y-%m-%d'),
        'slots': slots,
        'now': now.strftime('%Y-%m-%dT%H:%M:%S'),
    })

@login_required
def mis_citas(request):
    """Citas para choferes y vendedores"""
    if request.user.rol not in ['chofer', 'vendedor']:
        return redirect('clinica_dashboard')

    # Para vendedores y choferes: vehículos asignados
    if request.user.rol == 'vendedor':
        mis_patentes = Vehiculo.objects.filter(chofer_asignado=request.user).values_list('patente', flat=True)
    else:  # chofer
        # Primero buscar por chofer_asignado
        mis_patentes = Vehiculo.objects.filter(chofer_asignado=request.user).values_list('patente', flat=True)

        # Si no hay resultados, buscar por nombre (compatibilidad)
        if not mis_patentes:
            nombre_chofer = request.user.get_full_name() or request.user.username
            mis_patentes = Vehiculo.objects.filter(nombre_chofer__icontains=nombre_chofer).values_list('patente', flat=True)

    citas = CitaMantenimiento.objects.filter(
        Q(solicitante=request.user) | Q(patente__in=mis_patentes)
    ).select_related('vehiculo').order_by('fecha_hora')

    return render(request, 'agenda/mis_citas.html', {'citas': citas})

# ... (eliminar la segunda definición de mis_citas aquí) ...

@login_required
def lista_citas(request):
    if request.user.rol not in ['jefe_taller', 'admin']:
        return redirect('clinica_dashboard')

    # Incluir todas las citas con relaciones
    citas = CitaMantenimiento.objects.select_related(
        'vehiculo',
        'solicitante'
    ).order_by('-fecha_hora')  # Orden descendente para ver las más recientes primero

    return render(request, 'agenda/lista_citas_base.html', {'citas': citas})

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(CitaMantenimiento, id=cita_id)

    if request.method != 'POST':
        return redirect('agenda:detalle_cita', cita_id=cita_id)

    # Validar que la cita se pueda cancelar
    if cita.estado not in ['pendiente', 'confirmada']:
        messages.error(request, 'Esta cita ya no se puede cancelar.')
        return redirect('agenda:lista_citas')

    # Validar permisos
    puede_cancelar = (
        (request.user == cita.solicitante and request.user.rol == 'chofer') or
        request.user.rol in ['jefe_taller', 'admin']
    )

    if not puede_cancelar:
        messages.error(request, 'No tienes permiso para cancelar esta cita.')
        return redirect('clinica_dashboard')

    # Cancelar la cita
    cita.estado = 'cancelada'
    cita.save()

    # Mensaje y redirección según rol
    if request.user.rol == 'chofer':
        messages.info(request, 'Tu cita ha sido cancelada.')
        return redirect('agenda:mis_citas')
    else:
        messages.warning(request, f'Cita de {cita.patente} cancelada por {request.user.get_full_name() or request.user.username}.')
        return redirect('agenda:lista_citas')


@login_required
def detalle_cita(request, cita_id):
    cita = get_object_or_404(CitaMantenimiento, id=cita_id)
    # Solo permitir acceso si es el solicitante, jefe_taller o admin
    if not (
        request.user == cita.solicitante or
        request.user.rol in ['jefe_taller', 'admin']
    ):
        messages.error(request, 'No tienes permiso para ver esta cita.')
        return redirect('agenda:lista_citas')
    return render(request, 'agenda/detalle_cita_base.html', {'cita': cita})

@login_required
def eliminar_cita(request, cita_id):
    cita = get_object_or_404(CitaMantenimiento, id=cita_id)
    if request.method != 'POST':
        return redirect('agenda:detalle_cita', cita_id=cita_id)
    if request.user.rol not in ['jefe_taller', 'admin']:
        messages.error(request, 'No tienes permiso para eliminar esta cita.')
        return redirect('agenda:lista_citas')
    cita.delete()
    messages.success(request, 'Cita eliminada correctamente.')
    return redirect('agenda:lista_citas')

@login_required
def aceptar_cita(request, cita_id):
    cita = get_object_or_404(CitaMantenimiento, id=cita_id)
    if request.method != 'POST':
        return redirect('agenda:detalle_cita', cita_id=cita_id)
    if request.user.rol not in ['jefe_taller', 'admin']:
        messages.error(request, 'No tienes permiso para aceptar esta solicitud.')
        return redirect('agenda:lista_citas')
    if cita.estado == 'pendiente':
        cita.estado = 'confirmada'
        cita.save()
        messages.success(request, 'Solicitud aceptada.')
    else:
        messages.info(request, 'La solicitud ya no está pendiente.')
    return redirect('agenda:lista_citas')

@login_required
def completar_cita_patente(request, patente):
    if request.method != 'POST':
        return redirect('clinica_dashboard')
    if request.user.rol not in ['jefe_taller', 'admin']:
        messages.error(request, 'No tienes permiso para aprobar trabajos.')
        return redirect('clinica_dashboard')

    cita = CitaMantenimiento.objects.filter(
        patente=patente,
        tipo_mantencion='correctiva',
        estado__in=['pendiente', 'confirmada']
    ).order_by('-fecha_hora').first()

    if not cita:
        messages.warning(request, 'No se encontró una solicitud de reparación activa para esta patente.')
        return redirect('clinica_dashboard')

    cita.estado = 'completada'
    cita.save()
    messages.success(request, f'Trabajo aprobado para {patente}. Cita marcada como completada.')
    return redirect('clinica_dashboard')
