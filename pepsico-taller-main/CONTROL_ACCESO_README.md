# Sistema de Control de Acceso Vehicular - Guardia

## 📋 Descripción

Sistema de control de acceso vehicular para el taller PepsiCo, similar a un sistema de parking que registra todas las entradas y salidas de vehículos.

## ✨ Características

### Para el Guardia:
- ✅ **Registro de Entradas**: Registrar cuando un vehículo ingresa al taller
- ✅ **Registro de Salidas**: Registrar cuando un vehículo sale del taller
- ✅ **Panel de Control**: Vista general de vehículos en taller
- ✅ **Historial Completo**: Búsqueda y filtrado de todos los movimientos
- ✅ **Fotografías**: Captura de fotos en entrada y salida
- ✅ **Observaciones**: Registro de daños y estado del vehículo

### Información Registrada:

#### En la Entrada:
- Patente del vehículo
- Nombre del chofer
- Teléfono del chofer
- Empresa
- Kilometraje
- Observaciones (daños visibles, estado general)
- Foto del vehículo (opcional)
- Fecha y hora automática
- Guardia que registra

#### En la Salida:
- Nombre del chofer que retira
- Teléfono del chofer
- Kilometraje de salida
- Observaciones de entrega
- Foto del vehículo al salir (opcional)
- Fecha y hora automática
- Guardia que registra

## 🚀 Acceso al Sistema

### Para Guardias:

1. **Desde el Dashboard**:
   - Ir a `Dashboard de Guardia`
   - Click en "🎯 Ir al Panel de Control"

2. **Desde el Menú**:
   - Click en "Control Acceso" en el menú superior

3. **URL Directa**:
   - `/vehiculos/guardia/panel/`

## 📖 Guía de Uso

### Registrar Entrada de Vehículo

1. Ir al Panel de Guardia
2. Click en "Registrar Entrada de Vehículo"
3. Ingresar la patente (el vehículo debe estar registrado)
4. Completar datos del chofer
5. Registrar kilometraje actual
6. Agregar observaciones si hay daños visibles
7. Tomar foto (recomendado)
8. Click en "Registrar Entrada"

### Registrar Salida de Vehículo

1. Ir al Panel de Guardia
2. En la tabla "Vehículos en Taller", buscar el vehículo
3. Click en "Registrar Salida" (solo disponible si está "Listo para Retiro")
4. Completar datos del chofer que retira
5. Registrar kilometraje de salida
6. Agregar observaciones de entrega
7. Tomar foto (recomendado)
8. Click en "Confirmar Salida"

### Ver Historial de Accesos

1. Ir al Panel de Guardia
2. Click en "Ver Historial Completo"
3. Usar filtros:
   - Fecha desde/hasta
   - Patente
   - Tipo de movimiento (entrada/salida)
4. Click en "Buscar"

## 🗂️ Estructura de Archivos

```
vehiculos/
├── models.py                    # Modelo RegistroAcceso
├── forms.py                     # RegistroEntradaForm, RegistroSalidaForm
├── views_acceso.py             # Vistas del sistema de acceso
├── urls.py                      # Rutas del sistema
└── admin.py                     # Configuración admin

templates/vehiculos/guardia/
├── panel_guardia.html          # Panel principal
├── registrar_entrada.html      # Formulario de entrada
├── registrar_salida.html       # Formulario de salida
├── historial_acceso.html       # Historial con filtros
└── detalle_registro.html       # Detalle de un registro
```

## 🔐 Permisos

- **Guardia**: Acceso completo al sistema
- **Admin**: Acceso completo al sistema
- **Jefe de Taller**: Solo visualización de historial

## 📊 Modelo de Datos

### RegistroAcceso

| Campo | Tipo | Descripción |
|-------|------|-------------|
| vehiculo | ForeignKey | Vehículo relacionado |
| tipo_movimiento | CharField | 'entrada' o 'salida' |
| fecha_hora | DateTimeField | Timestamp automático |
| guardia | ForeignKey | Usuario guardia |
| nombre_chofer | CharField | Nombre del chofer |
| telefono_chofer | CharField | Teléfono del chofer |
| empresa_chofer | CharField | Empresa del chofer |
| kilometraje | IntegerField | Kilometraje registrado |
| observaciones | TextField | Observaciones generales |
| foto_vehiculo | ImageField | Foto del vehículo |
| autorizado_por | ForeignKey | Quien autoriza la salida |

## 🎯 URLs Disponibles

| URL | Nombre | Descripción |
|-----|--------|-------------|
| `/vehiculos/guardia/panel/` | panel_guardia | Panel principal |
| `/vehiculos/guardia/registrar-entrada/` | registrar_entrada | Registrar entrada |
| `/vehiculos/guardia/registrar-salida/<id>/` | registrar_salida | Registrar salida |
| `/vehiculos/guardia/historial/` | historial_acceso | Historial completo |
| `/vehiculos/guardia/registro/<id>/` | detalle_registro | Detalle de registro |

## 💡 Recomendaciones

1. **Siempre tomar fotos**: Ayuda a documentar el estado del vehículo
2. **Registrar observaciones**: Especialmente si hay daños visibles
3. **Verificar kilometraje**: Importante para el control
4. **Confirmar datos del chofer**: Asegurar que sean correctos
5. **Revisar estado del vehículo**: Antes de autorizar salida

## 🔄 Flujo de Trabajo

```
1. Vehículo llega al taller
   ↓
2. Guardia registra ENTRADA
   - Datos del vehículo
   - Datos del chofer
   - Foto y observaciones
   ↓
3. Vehículo en taller (trabajo en progreso)
   ↓
4. Mecánico marca como "Listo para Retiro"
   ↓
5. Guardia registra SALIDA
   - Datos del chofer que retira
   - Foto y observaciones
   - Kilometraje de salida
   ↓
6. Vehículo sale del taller
```

## 📝 Notas Importantes

- El vehículo **debe estar registrado** en el sistema antes de registrar entrada
- Solo se puede registrar salida si el vehículo está marcado como "Listo para Retiro"
- Todos los movimientos quedan registrados con fecha, hora y guardia responsable
- Las fotos se almacenan en `media/acceso_vehiculos/`

## 🐛 Solución de Problemas

### "El vehículo no está registrado"
- Primero debe registrarse el vehículo en "Nuevo Ingreso"

### "El vehículo ya está en el taller"
- Verificar en el historial si ya se registró la entrada

### "No se puede registrar salida"
- El vehículo debe estar en estado "Listo para Retiro"
- Contactar al jefe de taller para cambiar el estado

## 📞 Soporte

Para problemas o consultas, contactar al administrador del sistema.
