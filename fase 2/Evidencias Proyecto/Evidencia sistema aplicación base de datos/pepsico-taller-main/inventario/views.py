
# Create your views here.

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Repuesto, CategoriaRepuesto, MovimientoInventario, AjusteInventario, PedidoRepuesto
from .forms import RepuestoForm, MovimientoInventarioForm, AjusteInventarioForm, PedidoRepuestoForm
from .forms import CategoriaRepuestoForm
import sqlite3
import decimal
from django.conf import settings

# inventario/views.py
@login_required
def dashboard_inventario(request):
    try:
        # Métricas básicas
        total_repuestos = Repuesto.objects.count()
        repuestos_bajo_stock = Repuesto.objects.filter(estado='bajo_stock').count()
        repuestos_agotados = Repuesto.objects.filter(estado='agotado').count()
        
        # Valor total - cálculo simple y seguro
        valor_total = 0
        for repuesto in Repuesto.objects.all():
            try:
                # Asegurarnos de que los valores sean numéricos
                stock = repuesto.stock_actual or 0
                precio = float(repuesto.precio_costo or 0)
                valor_total += stock * precio
            except (TypeError, ValueError):
                # Si hay error en algún cálculo, continuar con los demás
                continue
        
        # Repuestos que necesitan reposición
        repuestos_reposicion = Repuesto.objects.filter(
            Q(estado='bajo_stock') | Q(estado='agotado')
        ).order_by('stock_actual')[:10]
        
        # Últimos movimientos
        ultimos_movimientos = MovimientoInventario.objects.select_related(
            'repuesto', 'usuario'
        ).order_by('-fecha_movimiento')[:10]
        
        context = {
            'total_repuestos': total_repuestos,
            'repuestos_bajo_stock': repuestos_bajo_stock,
            'repuestos_agotados': repuestos_agotados,
            'valor_total': round(valor_total, 2),
            'repuestos_reposicion': repuestos_reposicion,
            'ultimos_movimientos': ultimos_movimientos,
        }
        
    except Exception as e:
        # En caso de error, mostrar valores por defecto
        context = {
            'total_repuestos': 0,
            'repuestos_bajo_stock': 0,
            'repuestos_agotados': 0,
            'valor_total': 0,
            'repuestos_reposicion': [],
            'ultimos_movimientos': [],
        }
    
    return render(request, 'inventario/dashboard.html', context)

@login_required
def lista_repuestos(request):
    repuestos = Repuesto.objects.select_related('categoria').all()
    
    # Filtros
    estado = request.GET.get('estado')
    categoria_id = request.GET.get('categoria')
    search = request.GET.get('search')
    
    if estado:
        repuestos = repuestos.filter(estado=estado)
    if categoria_id:
        repuestos = repuestos.filter(categoria_id=categoria_id)
    if search:
        repuestos = repuestos.filter(
            Q(codigo__icontains=search) |
            Q(nombre__icontains=search) |
            Q(modelo_compatible__icontains=search) |
            Q(marca__icontains=search)
        )
    
    categorias = CategoriaRepuesto.objects.all()
    
    context = {
        'repuestos': repuestos,
        'categorias': categorias,
        'filtro_estado': estado,
        'filtro_categoria': categoria_id,
        'filtro_search': search,
    }
    return render(request, 'inventario/lista_repuestos.html', context)

@login_required
def detalle_repuesto(request, repuesto_id):
    repuesto = get_object_or_404(Repuesto, id=repuesto_id)
    movimientos = repuesto.movimientos.select_related('usuario', 'tarea').order_by('-fecha_movimiento')[:20]
    
    context = {
        'repuesto': repuesto,
        'movimientos': movimientos,
    }
    return render(request, 'inventario/detalle_repuesto.html', context)

@login_required
def crear_repuesto(request):
    if request.method == 'POST':
        form = RepuestoForm(request.POST)
        if form.is_valid():
            repuesto = form.save()
            messages.success(request, f'Repuesto {repuesto.codigo} creado exitosamente!')
            return redirect('lista_repuestos')
    else:
        form = RepuestoForm()
    
    return render(request, 'inventario/crear_repuesto.html', {'form': form})


@login_required
def editar_repuesto(request, repuesto_id):
    repuesto = get_object_or_404(Repuesto, id=repuesto_id)
    if request.method == 'POST':
        form = RepuestoForm(request.POST, instance=repuesto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Repuesto {repuesto.codigo} actualizado exitosamente!')
            return redirect('lista_repuestos')
    else:
        form = RepuestoForm(instance=repuesto)

    # Reutilizamos la plantilla de crear_repuesto pero cambiamos título/encabezado en el contexto
    return render(request, 'inventario/crear_repuesto.html', {
        'form': form,
        'editar': True,
        'repuesto_obj': repuesto,
    })

@login_required
def movimiento_entrada(request):
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.tipo_movimiento = 'entrada'
            movimiento.usuario = request.user
            movimiento.save()
            
            messages.success(request, f'Entrada de {movimiento.cantidad} unidades registrada para {movimiento.repuesto.nombre}')
            return redirect('dashboard_inventario')
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'inventario/movimiento_form.html', {
        'form': form,
        'titulo': 'Registrar Entrada de Inventario',
        'tipo_movimiento': 'entrada'
    })

@login_required
def movimiento_salida(request):
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.tipo_movimiento = 'salida'
            movimiento.usuario = request.user
            
            # Verificar stock suficiente
            if movimiento.repuesto.stock_actual < movimiento.cantidad:
                messages.error(request, f'Stock insuficiente. Stock actual: {movimiento.repuesto.stock_actual}')
                return render(request, 'inventario/movimiento_form.html', {
                    'form': form,
                    'titulo': 'Registrar Salida de Inventario',
                    'tipo_movimiento': 'salida'
                })
            
            movimiento.save()
            messages.success(request, f'Salida de {movimiento.cantidad} unidades registrada para {movimiento.repuesto.nombre}')
            return redirect('dashboard_inventario')
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'inventario/movimiento_form.html', {
        'form': form,
        'titulo': 'Registrar Salida de Inventario',
        'tipo_movimiento': 'salida'
    })

@login_required
def crear_ajuste(request):
    if request.method == 'POST':
        form = AjusteInventarioForm(request.POST)
        if form.is_valid():
            ajuste = form.save(commit=False)
            ajuste.usuario = request.user
            ajuste.cantidad_sistema = ajuste.repuesto.stock_actual
            ajuste.save()
            
            messages.success(request, f'Ajuste de inventario registrado para {ajuste.repuesto.nombre}')
            return redirect('dashboard_inventario')
    else:
        form = AjusteInventarioForm()
    
    return render(request, 'inventario/crear_ajuste.html', {'form': form})

@login_required
def crear_pedido(request):
    if request.method == 'POST':
        form = PedidoRepuestoForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.solicitante = request.user
            pedido.save()
            
            messages.success(request, f'Pedido {pedido.codigo_pedido} creado exitosamente!')
            return redirect('lista_pedidos')
    else:
        form = PedidoRepuestoForm()
    
    return render(request, 'inventario/crear_pedido.html', {'form': form})

@login_required
def lista_pedidos(request):
    # Intentamos usar ORM normalmente, pero algunos entornos pueden tener valores
    # corruptos en columnas DECIMAL (ej: cadenas vacías) que lanzan
    # decimal.InvalidOperation cuando Django intenta convertirlos. Capturamos
    # ese error y caemos a un fallback que consulta sqlite directamente y
    # devuelve una lista de dicts con campos seguros para renderizar.
    try:
        pedidos = PedidoRepuesto.objects.select_related('repuesto', 'solicitante').all()
        estado = request.GET.get('estado')
        # Por defecto no mostrar pedidos completados (se "quitan" al ser recibidos).
        if estado:
            pedidos = pedidos.filter(estado=estado)
        else:
            pedidos = pedidos.exclude(estado='completado')

        context = {
            'pedidos': pedidos,
            'filtro_estado': estado,
        }
        return render(request, 'inventario/lista_pedidos.html', context)

    except (decimal.InvalidOperation, Exception) as e:
        # Fallback seguro: leer con sqlite3 campos esenciales
        try:
            db_path = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            estado = request.GET.get('estado')
            # Si el usuario no filtra por estado, excluimos por defecto los pedidos completados
            if estado:
                sql = "SELECT id, codigo_pedido, repuesto_id, cantidad_solicitada, proveedor, estado, solicitante_id FROM inventario_pedidorepuesto WHERE estado = ?"
                params = [estado]
            else:
                sql = "SELECT id, codigo_pedido, repuesto_id, cantidad_solicitada, proveedor, estado, solicitante_id FROM inventario_pedidorepuesto WHERE estado != 'completado'"
                params = []
            cur.execute(sql, params)
            rows = cur.fetchall()
            pedidos_safe = []
            # Mapear repuesto_id y solicitante_id a nombres cuando sea posible
            # Recopilar IDs para lookup en batch
            repuesto_ids = list({r['repuesto_id'] for r in rows if r['repuesto_id'] is not None})
            solicitante_ids = list({r['solicitante_id'] for r in rows if r['solicitante_id'] is not None})

            # Obtener nombres de repuestos
            repuestos_map = {}
            if repuesto_ids:
                q = "SELECT id, nombre FROM inventario_repuesto WHERE id IN ({seq})".format(seq=','.join('?'*len(repuesto_ids)))
                cur.execute(q, repuesto_ids)
                for rr in cur.fetchall():
                    repuestos_map[rr['id']] = rr['nombre']

            # Obtener usernames de solicitantes
            usuarios_map = {}
            if solicitante_ids:
                q = "SELECT id, username FROM usuarios_usuario WHERE id IN ({seq})".format(seq=','.join('?'*len(solicitante_ids)))
                cur.execute(q, solicitante_ids)
                for uu in cur.fetchall():
                    usuarios_map[uu['id']] = uu['username']

            for r in rows:
                rep_nombre = repuestos_map.get(r['repuesto_id']) if r['repuesto_id'] else None
                sol_username = usuarios_map.get(r['solicitante_id']) if r['solicitante_id'] else None
                pedidos_safe.append({
                    'id': r['id'],
                    'codigo_pedido': r['codigo_pedido'],
                    'repuesto_nombre': rep_nombre,
                    'repuesto': {'id': r['repuesto_id']},
                    'cantidad_solicitada': r['cantidad_solicitada'],
                    'proveedor': r['proveedor'],
                    'estado': r['estado'],
                    'solicitante_username': sol_username,
                    'solicitante': {'id': r['solicitante_id']},
                })
            conn.close()

            # Renderizar con la lista segura. La plantilla puede acceder a los
            # atributos por clave; en caso que espere objetos, la resolución de
            # variables en Django templates también admite dicts.
            context = {
                'pedidos': pedidos_safe,
                'filtro_estado': estado,
            }
            return render(request, 'inventario/lista_pedidos.html', context)
        except Exception:
            # Si incluso el fallback falla, retornar página con mensaje vacío
            context = {
                'pedidos': [],
                'filtro_estado': request.GET.get('estado')
            }
            return render(request, 'inventario/lista_pedidos.html', context)


@login_required
def lista_categorias(request):
    categorias = CategoriaRepuesto.objects.all().order_by('nombre')
    return render(request, 'inventario/lista_categorias.html', {'categorias': categorias})


@login_required
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaRepuestoForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría "{categoria.nombre}" creada correctamente.')
            return redirect('lista_categorias')
    else:
        form = CategoriaRepuestoForm()
    return render(request, 'inventario/crear_categoria.html', {'form': form})

@login_required
def recibir_pedido(request, pedido_id):
    # Intentar obtener el objeto via ORM; si falla por problemas de conversión
    # (ej. valores DECIMAL corruptos) usamos un fallback que lee la fila con
    # sqlite3 y renderiza una representación segura (solo para GET).
    fallback = False
    try:
        pedido = get_object_or_404(PedidoRepuesto, id=pedido_id)
    except decimal.InvalidOperation:
        # Fallback seguro leyendo la fila directamente
        try:
            db_path = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = ("SELECT id, codigo_pedido, repuesto_id, cantidad_solicitada, cantidad_recibida, proveedor, "
                 "costo_unitario, costo_total, estado, solicitante_id FROM inventario_pedidorepuesto WHERE id = ?")
            cur.execute(q, (pedido_id,))
            r = cur.fetchone()
            if not r:
                conn.close()
                messages.error(request, 'Pedido no encontrado')
                return redirect('lista_pedidos')

            # Obtener nombre del repuesto si está disponible
            rep_nombre = None
            if r['repuesto_id']:
                cur.execute("SELECT nombre FROM inventario_repuesto WHERE id = ?", (r['repuesto_id'],))
                rr = cur.fetchone()
                if rr:
                    rep_nombre = rr['nombre']

            # Obtener username solicitante si está disponible
            sol_username = None
            if r['solicitante_id']:
                cur.execute("SELECT username FROM usuarios_usuario WHERE id = ?", (r['solicitante_id'],))
                uu = cur.fetchone()
                if uu:
                    sol_username = uu['username']

            pedido = {
                'id': r['id'],
                'codigo_pedido': r['codigo_pedido'],
                'repuesto_nombre': rep_nombre,
                'repuesto': {'id': r['repuesto_id']},
                'cantidad_solicitada': r['cantidad_solicitada'],
                'cantidad_recibida': r['cantidad_recibida'],
                'proveedor': r['proveedor'],
                'costo_unitario': r['costo_unitario'],
                'costo_total': r['costo_total'],
                'estado': r['estado'],
                'solicitante_username': sol_username,
                'solicitante': {'id': r['solicitante_id']},
            }
            conn.close()
            fallback = True
        except Exception:
            messages.error(request, 'Error al leer el pedido desde la base de datos')
            return redirect('lista_pedidos')

    # Si el cliente hace POST y estamos en modo fallback, no permitimos procesar
    # la recepción porque no podemos persistir con datos corruptos.
    if request.method == 'POST':
        if fallback:
            messages.error(request, 'No se puede procesar la recepción: el pedido contiene datos inconsistentes en la base. Contacte al administrador.')
            return redirect('lista_pedidos')

        # Parsear de forma robusta para evitar ValueError si el campo viene vacío
        cantidad_raw = request.POST.get('cantidad_recibida', 0)
        try:
            cantidad_recibida = int(cantidad_raw or 0)
        except (ValueError, TypeError):
            cantidad_recibida = 0

        costo_raw = request.POST.get('costo_unitario')
        costo_unitario = None
        if costo_raw:
            try:
                costo_unitario = float(costo_raw)
            except (ValueError, TypeError):
                costo_unitario = None

        if cantidad_recibida > 0:
            # Actualizar pedido (ORM)
            pedido.cantidad_recibida = cantidad_recibida
            if costo_unitario is not None:
                pedido.costo_unitario = costo_unitario
                pedido.costo_total = costo_unitario * cantidad_recibida

            if cantidad_recibida >= pedido.cantidad_solicitada:
                pedido.estado = 'completado'
            else:
                pedido.estado = 'parcial'

            pedido.fecha_recepcion = timezone.now()
            pedido.save()

            # Crear movimiento de entrada
            MovimientoInventario.objects.create(
                repuesto=pedido.repuesto,
                tipo_movimiento='entrada',
                cantidad=cantidad_recibida,
                usuario=request.user,
                motivo=f"Recepción de pedido {pedido.codigo_pedido}",
                numero_documento=pedido.codigo_pedido,
                costo_unitario=pedido.costo_unitario,
                stock_anterior=pedido.repuesto.stock_actual,
                stock_posterior=pedido.repuesto.stock_actual + cantidad_recibida
            )

            messages.success(request, f'Pedido {pedido.codigo_pedido} recibido exitosamente!')
            return redirect('lista_pedidos')

    return render(request, 'inventario/recibir_pedido.html', {'pedido': pedido, 'fallback': fallback})