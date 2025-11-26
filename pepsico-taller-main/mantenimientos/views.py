from django.shortcuts import render

# Create your views here.
# mantenimientos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Tarea, Pausa
from inventario.models import Repuesto, MovimientoInventario
from .forms import TareaForm, PausaForm,CompletarTareaForm

@login_required
def lista_tareas(request):
    tareas = Tarea.objects.all().order_by('-fecha_creacion')
    
    # Filtrar por estado si se especifica
    estado = request.GET.get('estado')
    if estado:
        tareas = tareas.filter(estado=estado)
    
    # Filtrar por mecánico si es mecánico
    if request.user.rol == 'mecanico':
        tareas = tareas.filter(mecanico_asignado=request.user)
    
    return render(request, 'mantenimientos/lista_tareas.html', {'tareas': tareas})

@login_required
def crear_tarea(request):
    if request.user.rol not in ['jefe_taller', 'admin']:
        messages.error(request, 'No tienes permisos para crear tareas.')
        return redirect('lista_tareas')
    vehiculo_id = request.GET.get('vehiculo')
    initial = {}
    if vehiculo_id:
        initial['vehiculo'] = vehiculo_id

    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save()
            messages.success(request, f'Tarea "{tarea.titulo}" creada exitosamente!')
            return redirect('detalle_vehiculo', vehiculo_id=tarea.vehiculo.id)
    else:
        form = TareaForm(initial=initial)
    
    return render(request, 'mantenimientos/crear_tarea.html', {'form': form})


@login_required
def editar_tarea(request, tarea_id):
    """Editar una tarea existente"""
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Permisos: jefe_taller y admin pueden editar cualquier tarea; el mecánico asignado puede editar la suya
    if request.user.rol not in ['jefe_taller', 'admin'] and tarea.mecanico_asignado != request.user:
        messages.error(request, 'No tienes permiso para editar esta tarea.')
        return redirect('lista_tareas')

    if request.method == 'POST':
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            tarea = form.save()
            messages.success(request, f'Tarea "{tarea.titulo}" actualizada exitosamente!')
            return redirect('detalle_tarea', tarea_id=tarea.id)
    else:
        form = TareaForm(instance=tarea)

    return render(request, 'mantenimientos/crear_tarea.html', {
        'form': form,
        'editar': True,
        'tarea_obj': tarea,
    })

@login_required
def iniciar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    if tarea.mecanico_asignado != request.user and request.user.rol != 'jefe_taller':
        messages.error(request, 'No tienes permiso para trabajar en esta tarea.')
        return redirect('lista_tareas')
    
    tarea.estado = 'en_proceso'
    tarea.fecha_inicio = timezone.now()
    tarea.save()
    
    messages.success(request, f'Tarea "{tarea.titulo}" iniciada.')
    return redirect('lista_tareas')

@login_required
def pausar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    if request.method == 'POST':
        form = PausaForm(request.POST)
        if form.is_valid():
            pausa = form.save(commit=False)
            pausa.tarea = tarea
            pausa.save()
            
            tarea.estado = 'pausada'
            tarea.save()
            
            messages.info(request, f'Tarea pausada: {pausa.get_motivo_display()}')
            return redirect('lista_tareas')
    else:
        form = PausaForm()
    
    return render(request, 'mantenimientos/pausar_tarea.html', {'form': form, 'tarea': tarea})


@login_required
def pausar_rapida(request, tarea_id):
    """Crea una pausa rápida (motivo 'otro' opcional) vía POST para flow rápido en UI móvil/rápido."""
    from django.shortcuts import get_object_or_404
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Permisos: solo mecánico asignado o jefe_taller
    if tarea.mecanico_asignado != request.user and request.user.rol != 'jefe_taller':
        messages.error(request, 'No tienes permiso para pausar esta tarea.')
        return redirect('detalle_tarea', tarea_id=tarea_id)

    if request.method == 'POST':
        motivo = request.POST.get('motivo', 'otro')
        motivo_otro = request.POST.get('motivo_otro', '')

        pausa = Pausa.objects.create(
            tarea=tarea,
            motivo=motivo,
            motivo_otro=motivo_otro,
        )

        tarea.estado = 'pausada'
        tarea.save()

        messages.info(request, f'Pausa iniciada: {pausa.get_motivo_display()}')
    return redirect('detalle_tarea', tarea_id=tarea_id)


@login_required
def terminar_pausa(request, tarea_id):
    """Finaliza la pausa activa de una tarea (POST)."""
    tarea = get_object_or_404(Tarea, id=tarea_id)

    # Permisos: mecánico asignado o jefe_taller
    if tarea.mecanico_asignado != request.user and request.user.rol != 'jefe_taller':
        messages.error(request, 'No tienes permiso para finalizar la pausa.')
        return redirect('detalle_tarea', tarea_id=tarea_id)

    if request.method == 'POST':
        pausa_activa = tarea.pausas.filter(fecha_fin__isnull=True).first()
        if pausa_activa:
            pausa_activa.fecha_fin = timezone.now()
            pausa_activa.save()
            messages.success(request, 'Pausa finalizada.')
        else:
            messages.info(request, 'No hay pausa activa para finalizar.')

        tarea.estado = 'en_proceso'
        tarea.save()

    return redirect('detalle_tarea', tarea_id=tarea_id)


@login_required
def detalle_tarea(request, tarea_id):
    """Muestra el detalle completo de una tarea"""
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Obtener pausas relacionadas (si existen)
    pausas = tarea.pausas.all().order_by('-fecha_inicio')
    
    context = {
        'tarea': tarea,
        'pausas': pausas,
    }
    return render(request, 'mantenimientos/detalle_tarea.html', context)

@login_required
def reanudar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Finalizar la pausa activa
    pausa_activa = tarea.pausas.filter(fecha_fin__isnull=True).first()
    if pausa_activa:
        pausa_activa.fecha_fin = timezone.now()
        pausa_activa.save()
    
    tarea.estado = 'en_proceso'
    tarea.save()
    
    messages.success(request, f'Tarea "{tarea.titulo}" reanudada.')
    return redirect('lista_tareas')



#------------------------------------------------------------
# mantenimientos/views.py - AGREGAR
@login_required
def completar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    # Verificar permisos
    if tarea.mecanico_asignado != request.user and request.user.rol not in ['jefe_taller', 'admin']:
        messages.error(request, 'No tienes permiso para completar esta tarea.')
        return redirect('lista_tareas')
    
    if request.method == 'POST':
        form = CompletarTareaForm(request.POST, instance=tarea)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.estado = 'completada'
            tarea.fecha_fin = timezone.now()
            tarea.save()
            
            messages.success(request, f'Tarea "{tarea.titulo}" completada exitosamente!')
            return redirect('lista_tareas')
    else:
        form = CompletarTareaForm(instance=tarea)
    
    return render(request, 'mantenimientos/completar_tarea.html', {
        'tarea': tarea,
        'form': form
    })


@login_required
def gestionar_repuestos_tarea(request, tarea_id):
    """Gestionar repuestos utilizados en una tarea"""
    tarea = get_object_or_404(Tarea, id=tarea_id)
    
    if request.method == 'POST':
        repuesto_id = request.POST.get('repuesto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        
        if repuesto_id and cantidad > 0:
            repuesto = get_object_or_404(Repuesto, id=repuesto_id)
            
            # Verificar stock
            if repuesto.stock_actual < cantidad:
                messages.error(request, f'Stock insuficiente. Stock actual: {repuesto.stock_actual}')
                return redirect('gestionar_repuestos_tarea', tarea_id=tarea_id)
            
            # Crear movimiento de salida
            MovimientoInventario.objects.create(
                repuesto=repuesto,
                tipo_movimiento='salida',
                cantidad=cantidad,
                usuario=request.user,
                tarea=tarea,
                motivo=f"Uso en tarea: {tarea.titulo}",
                stock_anterior=repuesto.stock_actual,
                stock_posterior=repuesto.stock_actual - cantidad
            )
            
            messages.success(request, f'Repuesto {repuesto.nombre} utilizado en la tarea.')
    
    # Repuestos utilizados en esta tarea
    repuestos_utilizados = MovimientoInventario.objects.filter(
        tarea=tarea, 
        tipo_movimiento='salida'
    ).select_related('repuesto')
    
    # Repuestos disponibles
    repuestos_disponibles = Repuesto.objects.filter(stock_actual__gt=0)
    
    return render(request, 'mantenimientos/gestionar_repuestos_tarea.html', {
        'tarea': tarea,
        'repuestos_utilizados': repuestos_utilizados,
        'repuestos_disponibles': repuestos_disponibles,
    })
