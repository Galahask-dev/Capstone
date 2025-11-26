# reportes/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied # Importar PermissionDenied
from django.utils import timezone
from django.utils.timesince import timesince
from datetime import timedelta, datetime
from django.db.models import Count, Avg, Sum, Q, ExpressionWrapper, F, FloatField, DurationField
from django.db.models.functions import ExtractHour, ExtractMinute
from vehiculos.models import Vehiculo
from mantenimientos.models import Tarea, Pausa
from usuarios.models import Usuario


@login_required
def dashboard_reportes(request):
    # 🔒 Verificación de rol para acceso a reportes
    if request.user.rol not in ['jefe_taller', 'admin']:
        raise PermissionDenied("No tienes permiso para acceder a este reporte.")
    # Fin de la verificación de rol

    # Fechas para filtros
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    # Métricas generales
    total_vehiculos = Vehiculo.objects.count()
    vehiculos_taller = Vehiculo.objects.exclude(estado='entregado').count()
    tareas_completadas = Tarea.objects.filter(estado='completada').count()
    tareas_pendientes = Tarea.objects.filter(estado__in=['pendiente', 'en_proceso', 'pausada']).count()
    
    # Eficiencia del taller
    vehiculos_completados = Vehiculo.objects.filter(estado='entregado', fecha_salida__isnull=False)
    tiempo_promedio_taller = 0
    if vehiculos_completados.exists():
        tiempos = []
        for v in vehiculos_completados:
            tiempo = (v.fecha_salida - v.fecha_ingreso).total_seconds() / 3600  # Horas
            tiempos.append(tiempo)
        if tiempos:
            tiempo_promedio_taller = sum(tiempos) / len(tiempos)
    
    # Análisis de pausas
    pausas_ultima_semana = Pausa.objects.filter(
        fecha_inicio__date__gte=inicio_semana
    )
    
    # Calcular duración de pausas manualmente
    motivos_pausa_data = {}
    for pausa in pausas_ultima_semana:
        if pausa.fecha_fin:
            duracion = (pausa.fecha_fin - pausa.fecha_inicio).total_seconds() / 60  # Minutos
        else:
            duracion = 0
            
        motivo = pausa.get_motivo_display()
        if motivo not in motivos_pausa_data:
            motivos_pausa_data[motivo] = {
                'total': 0,
                'duracion_total': 0,
                'duracion_promedio': 0
            }
        
        motivos_pausa_data[motivo]['total'] += 1
        motivos_pausa_data[motivo]['duracion_total'] += duracion
    
    # Calcular promedios
    motivos_pausa = []
    for motivo, datos in motivos_pausa_data.items():
        if datos['total'] > 0:
            datos['duracion_promedio'] = datos['duracion_total'] / datos['total']
        else:
            datos['duracion_promedio'] = 0
        motivos_pausa.append({
            'motivo': motivo,
            'total': datos['total'],
            'duracion_promedio': datos['duracion_promedio']
        })
    
    # Ordenar por total descendente
    motivos_pausa.sort(key=lambda x: x['total'], reverse=True)
    
    # Productividad por mecánico - CORREGIDO
    from django.db.models import Case, When, Value
    
    productividad_mecanicos = Usuario.objects.filter(rol='mecanico').annotate(
        tareas_completadas=Count('tarea', filter=Q(tarea__estado='completada')),
        tareas_totales=Count('tarea')
    )
    
    # Calcular eficiencia manualmente
    mecanicos_data = []
    for mecanico in productividad_mecanicos:
        eficiencia = 0
        if mecanico.tareas_totales > 0:
            eficiencia = (mecanico.tareas_completadas / mecanico.tareas_totales) * 100
        
        mecanicos_data.append({
            'username': mecanico.username,
            'first_name': mecanico.first_name,
            'last_name': mecanico.last_name,
            'tareas_completadas': mecanico.tareas_completadas,
            'tareas_totales': mecanico.tareas_totales,
            'eficiencia': eficiencia
        })
    
    # Vehículos por estado (para gráfico)
    vehiculos_por_estado = Vehiculo.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    # Tareas por prioridad
    tareas_por_prioridad = Tarea.objects.values('prioridad').annotate(
        total=Count('id')
    ).order_by('prioridad')
    
    # Tiempos de respuesta de tareas
    tareas_completadas_con_tiempo = Tarea.objects.filter(
        estado='completada',
        fecha_inicio__isnull=False,
        fecha_fin__isnull=False
    )
    
    tiempo_promedio_tarea = 0
    if tareas_completadas_con_tiempo.exists():
        tiempos_tareas = []
        for tarea in tareas_completadas_con_tiempo:
            tiempo = (tarea.fecha_fin - tarea.fecha_inicio).total_seconds() / 3600  # Horas
            tiempos_tareas.append(tiempo)
        
        if tiempos_tareas:
            tiempo_promedio_tarea = sum(tiempos_tareas) / len(tiempos_tareas)

    # Flujo de Vehículos (Hoy)
    ingresos_hoy_qs = Vehiculo.objects.filter(fecha_ingreso__date=hoy).select_related('guardia_ingreso')
    vehiculos_ingreso_hoy = ingresos_hoy_qs.count()
    vehiculos_en_proceso = Vehiculo.objects.filter(estado__in=['diagnostico', 'reparacion']).count()
    salidas_hoy_qs = Vehiculo.objects.filter(fecha_salida__date=hoy).select_related('mecanico_asignado')
    vehiculos_salida_hoy = salidas_hoy_qs.count()

    proxima_accion_map = {
        'pendiente': 'Aprobar ingreso',
        'ingresado': 'Iniciar diagnóstico',
        'diagnostico': 'Pasar a reparación',
        'reparacion': 'Marcar listo',
        'listo': 'Entregar',
        'entregado': '—',
        'rechazado': '—',
    }

    vehiculos_flujo_qs = Vehiculo.objects.exclude(estado='entregado').select_related('mecanico_asignado', 'guardia_ingreso').order_by('-fecha_ingreso')
    vehiculos_flujo = []
    now = timezone.now()
    for v in vehiculos_flujo_qs:
        if v.estado == 'entregado' and v.fecha_salida and v.fecha_ingreso:
            tiempo_estado = timesince(v.fecha_ingreso, v.fecha_salida)
        elif v.fecha_ingreso:
            tiempo_estado = timesince(v.fecha_ingreso, now)
        else:
            tiempo_estado = None

        vehiculos_flujo.append({
            'patente': v.patente,
            'estado': v.estado,
            'get_estado_display': v.get_estado_display(),
            'tiempo_en_estado': tiempo_estado,
            'proxima_accion': proxima_accion_map.get(v.estado, '—'),
            'mecanico': v.mecanico_asignado.get_full_name() if getattr(v, 'mecanico_asignado', None) else None,
            'guardia': v.guardia_ingreso.get_full_name() if getattr(v, 'guardia_ingreso', None) else None,
            'fecha_ingreso': v.fecha_ingreso,
        })
    
    context = {
        'total_vehiculos': total_vehiculos,
        'vehiculos_taller': vehiculos_taller,
        'tareas_completadas': tareas_completadas,
        'tareas_pendientes': tareas_pendientes,
        'tiempo_promedio_taller': round(tiempo_promedio_taller, 1),
        'tiempo_promedio_tarea': round(tiempo_promedio_tarea, 1),
        'motivos_pausa': motivos_pausa,
        'productividad_mecanicos': mecanicos_data,
        'vehiculos_por_estado': list(vehiculos_por_estado),
        'tareas_por_prioridad': list(tareas_por_prioridad),
        'inicio_semana': inicio_semana,
        'hoy': hoy,
        'vehiculos_ingreso_hoy': vehiculos_ingreso_hoy,
        'vehiculos_en_proceso': vehiculos_en_proceso,
        'vehiculos_salida_hoy': vehiculos_salida_hoy,
        'vehiculos_flujo': vehiculos_flujo,
        'ingresos_hoy': ingresos_hoy_qs,
        'salidas_hoy': salidas_hoy_qs,
    }
    
    return render(request, 'reportes/dashboard.html', context)


@login_required
def reporte_productividad(request):
    """Reporte detallado de productividad por mecánico con métricas específicas"""
    # 🔒 Verificación de rol para acceso a reportes
    if request.user.rol not in ['jefe_taller', 'admin']:
        raise PermissionDenied("No tienes permiso para acceder a este reporte.")
    # Fin de la verificación de rol

    from datetime import timedelta
    from django.db.models import Count, Avg, Sum
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Normalize and parse dates: ignore 'None' strings or invalid formats
    if fecha_inicio in (None, '', 'None'):
        fecha_inicio = None
    if fecha_fin in (None, '', 'None'):
        fecha_fin = None

    from django.utils.dateparse import parse_date
    parsed_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    parsed_fin = parse_date(fecha_fin) if fecha_fin else None

    # Normalize parameters: ignore 'None' string or empty strings
    if fecha_inicio in (None, '', 'None'):
        fecha_inicio = None
    if fecha_fin in (None, '', 'None'):
        fecha_fin = None

    # Try to parse dates to ensure valid format, otherwise ignore the filter
    from django.utils.dateparse import parse_date
    parsed_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    parsed_fin = parse_date(fecha_fin) if fecha_fin else None
    
    mecanicos = Usuario.objects.filter(rol='mecanico')
    productividad_data = []
    
    for mecanico in mecanicos:
        # Base queryset para tareas
        tareas = Tarea.objects.filter(mecanico_asignado=mecanico)
        
        # Aplicar filtros de fecha si existen
        if fecha_inicio:
            tareas = tareas.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            tareas = tareas.filter(fecha_creacion__date__lte=fecha_fin)
        
        # Métricas específicas
        tareas_completadas = tareas.filter(estado='completada')
        tareas_en_proceso = tareas.filter(estado='en_proceso')
        tareas_pausadas = tareas.filter(estado='pausada')
        tareas_pendientes = tareas.filter(estado='pendiente')
        
        # Tiempos de trabajo
        tiempo_total_trabajado = timedelta()
        tiempos_por_tarea = []
        
        for tarea in tareas_completadas:
            if tarea.fecha_inicio and tarea.fecha_fin:
                tiempo_tarea = tarea.fecha_fin - tarea.fecha_inicio
                tiempo_total_trabajado += tiempo_tarea
                tiempos_por_tarea.append(tiempo_tarea.total_seconds() / 3600)  # Horas
        
        # Cálculo de eficiencia y métricas
        total_tareas = tareas.count()
        completadas_count = tareas_completadas.count()
        
        # Eficiencia
        eficiencia = (completadas_count / total_tareas * 100) if total_tareas > 0 else 0
        
        # Tiempo promedio por tarea
        tiempo_promedio = sum(tiempos_por_tarea) / len(tiempos_por_tarea) if tiempos_por_tarea else 0
        
        # Cumplimiento de tiempos estimados
        tareas_con_tiempo = tareas_completadas.filter(tiempo_estimado__isnull=False)
        cumplimiento_tiempos = 0
        if tareas_con_tiempo.exists():
            cumplimientos = []
            for tarea in tareas_con_tiempo:
                if tarea.fecha_inicio and tarea.fecha_fin:
                    tiempo_real = (tarea.fecha_fin - tarea.fecha_inicio).total_seconds() / 60  # Minutos
                    tiempo_estimado = tarea.tiempo_estimado
                    if tiempo_estimado > 0:
                        cumplimiento = (tiempo_estimado / tiempo_real * 100) if tiempo_real > 0 else 0
                        cumplimientos.append(min(cumplimiento, 200))  # Limitar a 200%
            if cumplimientos:
                cumplimiento_tiempos = sum(cumplimientos) / len(cumplimientos)
        
        # Análisis de pausas
        total_pausas = Pausa.objects.filter(tarea__mecanico_asignado=mecanico).count()
        pausas_activas = Pausa.objects.filter(tarea__mecanico_asignado=mecanico, fecha_fin__isnull=True).count()
        
        productividad_data.append({
            'mecanico': mecanico,
            'tareas_totales': total_tareas,
            'tareas_completadas': completadas_count,
            'tareas_en_proceso': tareas_en_proceso.count(),
            'tareas_pausadas': tareas_pausadas.count(),
            'tareas_pendientes': tareas_pendientes.count(),
            'eficiencia': eficiencia,
            'tiempo_total_trabajado': tiempo_total_trabajado,
            'tiempo_promedio_tarea': tiempo_promedio,
            'cumplimiento_tiempos': cumplimiento_tiempos,
            'total_pausas': total_pausas,
            'pausas_activas': pausas_activas,
            'tiempos_por_tarea': tiempos_por_tarea,
        })
    
    # Ordenar por eficiencia descendente
    productividad_data.sort(key=lambda x: x['eficiencia'], reverse=True)
    total_mecanicos = len(productividad_data)
    total_tareas = sum(d['tareas_totales'] for d in productividad_data) if productividad_data else 0
    prom_eficiencia = round((sum(d['eficiencia'] for d in productividad_data) / total_mecanicos), 1) if total_mecanicos else 0
    total_pausas = sum(d['total_pausas'] for d in productividad_data) if productividad_data else 0

    context = {
        'productividad_data': productividad_data,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_mecanicos': total_mecanicos,
        'total_tareas': total_tareas,
        'prom_eficiencia': prom_eficiencia,
        'total_pausas': total_pausas,
    }
    
    return render(request, 'reportes/reporte_productividad.html', context)


@login_required
def reporte_productividad_detalle(request, mecanico_id):
    """Detalle de productividad para un mecánico: lista de tareas y métricas"""
    # 🔒 Verificación de rol para acceso a reportes
    if request.user.rol not in ['jefe_taller', 'admin']:
        raise PermissionDenied("No tienes permiso para acceder a este reporte.")
    # Fin de la verificación de rol

    mecanico = get_object_or_404(Usuario, pk=mecanico_id, rol='mecanico')

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Normalize and parse dates: ignore 'None' string or empty strings
    if fecha_inicio in (None, '', 'None'):
        fecha_inicio = None
    if fecha_fin in (None, '', 'None'):
        fecha_fin = None

    from django.utils.dateparse import parse_date
    parsed_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    parsed_fin = parse_date(fecha_fin) if fecha_fin else None

    tareas_qs = Tarea.objects.filter(mecanico_asignado=mecanico)
    if parsed_inicio:
        tareas_qs = tareas_qs.filter(fecha_creacion__date__gte=parsed_inicio)
    if parsed_fin:
        tareas_qs = tareas_qs.filter(fecha_creacion__date__lte=parsed_fin)

    tareas_completadas_qs = tareas_qs.filter(estado='completada')

    tareas_list = []
    tiempo_total = 0.0
    tiempos_por_tarea = []

    for tarea in tareas_completadas_qs:
        tiempo_horas = None
        if tarea.fecha_inicio and tarea.fecha_fin:
            tiempo_horas = (tarea.fecha_fin - tarea.fecha_inicio).total_seconds() / 3600.0
            tiempos_por_tarea.append(tiempo_horas)
            tiempo_total += tiempo_horas

    # Prepare full tareas list including tiempo_horas for each
    for tarea in tareas_qs.order_by('-fecha_creacion'):
        th = None
        if tarea.fecha_inicio and tarea.fecha_fin:
            th = (tarea.fecha_fin - tarea.fecha_inicio).total_seconds() / 3600.0
        tareas_list.append({'tarea': tarea, 'tiempo_horas': th})

    tiempo_promedio = (sum(tiempos_por_tarea) / len(tiempos_por_tarea)) if tiempos_por_tarea else 0

    context = {
        'mecanico': mecanico,
        'tareas': tareas_list,
        'tareas_completadas_count': tareas_completadas_qs.count(),
        'tareas_totales': tareas_qs.count(),
        'tiempo_total': tiempo_total,
        'tiempo_promedio': tiempo_promedio,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'reportes/reporte_productividad_detalle.html', context)

@login_required
def reporte_tiempos_pausas(request):
    # Reporte detallado de tiempos y pausas
    # 🔒 Verificación de rol para acceso a reportes
    if request.user.rol not in ['jefe_taller', 'admin']:
        raise PermissionDenied("No tienes permiso para acceder a este reporte.")
    # Fin de la verificación de rol

    pausas_qs = Pausa.objects.select_related('tarea', 'tarea__vehiculo', 'tarea__mecanico_asignado')
    now = timezone.now()
    pausas_con_duracion = []  # pausas finalizadas
    pausas_activas = []       # pausas en curso (sin fecha_fin)
    for pausa in pausas_qs:
        if pausa.fecha_fin:
            duracion = (pausa.fecha_fin - pausa.fecha_inicio).total_seconds() / 60  # Minutos
            pausas_con_duracion.append({
                'pausa': pausa,
                'duracion_minutos': duracion,
                'duracion_horas': duracion / 60,
            })
        else:
            duracion = (now - pausa.fecha_inicio).total_seconds() / 60
            pausas_activas.append({
                'pausa': pausa,
                'duracion_minutos': duracion,
                'duracion_horas': duracion / 60,
            })
    
    # Agrupar por motivo
    pausas_por_motivo = {}
    for pausa_data in pausas_con_duracion:
        motivo = pausa_data['pausa'].get_motivo_display()
        if motivo not in pausas_por_motivo:
            pausas_por_motivo[motivo] = {
                'cantidad': 0,
                'tiempo_total_minutos': 0,
                'pausas': []
            }
        pausas_por_motivo[motivo]['cantidad'] += 1
        pausas_por_motivo[motivo]['tiempo_total_minutos'] += pausa_data['duracion_minutos']
        pausas_por_motivo[motivo]['pausas'].append(pausa_data)

    for motivo, datos in pausas_por_motivo.items():
        if datos['cantidad'] > 0:
            datos['promedio_minutos'] = datos['tiempo_total_minutos'] / datos['cantidad']
        else:
            datos['promedio_minutos'] = 0

    grafico_pausas_labels = list(pausas_por_motivo.keys())
    grafico_pausas_totales = [datos['tiempo_total_minutos'] for datos in pausas_por_motivo.values()]
    
    return render(request, 'reportes/reporte_tiempos_pausas.html', {
        'pausas_por_motivo': pausas_por_motivo,
        'pausas_totales': len(pausas_con_duracion),
        'pausas_activas': pausas_activas,
        'pausas_activas_count': len(pausas_activas),
        'grafico_pausas_labels': grafico_pausas_labels,
        'grafico_pausas_totales': grafico_pausas_totales,
    })

@login_required
def reporte_tiempos_taller(request):
    """Reporte específico de tiempos e inactividad de vehículos"""
    # 🔒 Verificación de rol para acceso a reportes
    if request.user.rol not in ['jefe_taller', 'admin']:
        raise PermissionDenied("No tienes permiso para acceder a este reporte.")
    # Fin de la verificación de rol

    from datetime import timedelta
    
    # Filtros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Base queryset
    vehiculos = Vehiculo.objects.all()
    
    # Aplicar filtros de fecha si existen
    if fecha_inicio:
        vehiculos = vehiculos.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_fin:
        vehiculos = vehiculos.filter(fecha_ingreso__date__lte=fecha_fin)
    
    # Vehículos actualmente en taller (excluyendo entregados)
    vehiculos_en_taller = vehiculos.exclude(estado='entregado')
    
    # Vehículos completados en el período
    vehiculos_completados = vehiculos.filter(estado='entregado', fecha_salida__isnull=False)
    
    # Cálculo de tiempos
    tiempos_analisis = []
    
    for vehiculo in vehiculos_en_taller:
        tiempo_en_taller = timezone.now() - vehiculo.fecha_ingreso
        horas_en_taller = tiempo_en_taller.total_seconds() / 3600
        
        tiempos_analisis.append({
            'vehiculo': vehiculo,
            'tiempo_horas': round(horas_en_taller, 1),
            'tiempo_dias': round(horas_en_taller / 24, 1),
            'estado_actual': vehiculo.get_estado_display(),
            'mecanico': vehiculo.mecanico_asignado
        })
    
    # Ordenar por tiempo descendente (los más antiguos primero)
    tiempos_analisis.sort(key=lambda x: x['tiempo_horas'], reverse=True)
    
    # Tiempos de vehículos completados
    tiempos_completados = []
    for vehiculo in vehiculos_completados:
        if vehiculo.fecha_salida:
            tiempo_total = vehiculo.fecha_salida - vehiculo.fecha_ingreso
            horas_total = tiempo_total.total_seconds() / 3600
            
            tiempos_completados.append({
                'vehiculo': vehiculo,
                'tiempo_horas': round(horas_total, 1),
                'tiempo_dias': round(horas_total / 24, 1)
            })
    
    # Estadísticas generales
    if tiempos_completados:
        tiempo_promedio_completados = sum(t['tiempo_horas'] for t in tiempos_completados) / len(tiempos_completados)
        tiempo_maximo_completados = max(t['tiempo_horas'] for t in tiempos_completados)
        tiempo_minimo_completados = min(t['tiempo_horas'] for t in tiempos_completados)
    else:
        tiempo_promedio_completados = tiempo_maximo_completados = tiempo_minimo_completados = 0
    
    # Tiempos por estado actual
    tiempos_por_estado = {}
    for item in tiempos_analisis:
        estado = item['estado_actual']
        if estado not in tiempos_por_estado:
            tiempos_por_estado[estado] = {
                'count': 0,
                'total_horas': 0,
                'vehiculos': []
            }
        tiempos_por_estado[estado]['count'] += 1
        tiempos_por_estado[estado]['total_horas'] += item['tiempo_horas']
        tiempos_por_estado[estado]['vehiculos'].append(item)
    
    # Calcular promedios por estado
    for estado, data in tiempos_por_estado.items():
        if data['count'] > 0:
            data['promedio_horas'] = round(data['total_horas'] / data['count'], 1)
        else:
            data['promedio_horas'] = 0
    
    context = {
        'vehiculos_en_taller': vehiculos_en_taller,
        'vehiculos_completados': vehiculos_completados,
        'tiempos_analisis': tiempos_analisis[:20],  # Top 20 más antiguos
        'tiempos_completados': tiempos_completados[:10],  # Top 10 más recientes
        'tiempos_por_estado': tiempos_por_estado,
        'estadisticas': {
            'total_en_taller': len(tiempos_analisis),
            'total_completados': len(tiempos_completados),
            'tiempo_promedio_completados': round(tiempo_promedio_completados, 1),
            'tiempo_maximo_completados': round(tiempo_maximo_completados, 1),
            'tiempo_minimo_completados': round(tiempo_minimo_completados, 1),
        },
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'reportes/reporte_tiempos_taller.html', context)
