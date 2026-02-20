# Manual de Usuario — Field Service · Hojas de Trabajo
**Módulo Odoo 19 · Econovex**

---

## Índice
1. [Acceso al módulo](#1-acceso-al-módulo)
2. [Grupos de usuarios](#2-grupos-de-usuarios)
3. [Crear un técnico (usuario de portal)](#3-crear-un-técnico-usuario-de-portal)
4. [Crear una Orden de Servicio](#4-crear-una-orden-de-servicio)
5. [Flujo de estados](#5-flujo-de-estados)
6. [Registrar materiales y horas](#6-registrar-materiales-y-horas)
7. [Registrar pagos en campo](#7-registrar-pagos-en-campo)
8. [Capturar la firma del cliente](#8-capturar-la-firma-del-cliente)
9. [Reportes e impresión](#9-reportes-e-impresión)
10. [Portal del técnico (acceso externo)](#10-portal-del-técnico-acceso-externo)
11. [Preguntas frecuentes](#11-preguntas-frecuentes)

---

## 1. Acceso al módulo

Desde el menú principal de Odoo seleccioná **"Servicios en Campo"**.

Verás dos opciones según tu rol:

| Menú | Quién lo ve | Qué muestra |
|------|-------------|-------------|
| **Todas las Órdenes** | Solo Gerentes | Todas las órdenes de la empresa |
| **Mis Órdenes** | Usuarios internos | Las órdenes donde sos responsable |
| **Mis Asignaciones** | Todos | Las órdenes donde estás como técnico |

La vista por defecto es **Kanban**, agrupada por estado. También podés cambiar a **Lista** o **Formulario**.

---

## 2. Grupos de usuarios

El módulo tiene dos grupos internos. Se asignan en **Ajustes → Usuarios → [usuario] → pestaña Accesos**.

| Grupo | Qué puede hacer |
|-------|-----------------|
| **Usuario de Servicios** | Crear y gestionar sus propias órdenes y las que tiene asignadas |
| **Gerente de Servicios** | Acceso completo: ver todas las órdenes, configuración |

> Los **técnicos externos** usan el portal (no consumen licencia Odoo). Ver sección 3.

---

## 3. Crear un técnico (usuario de portal)

Si el técnico es **externo** (no empleado con acceso completo a Odoo):

1. Ir a **Ajustes → Usuarios → Usuarios**
2. Hacer clic en **"Nuevo"**
3. Completar:
   - **Nombre** del técnico
   - **Email** (será su usuario de acceso)
   - En la sección de accesos, dejar el perfil en **"Portal"**
4. Guardar — Odoo enviará automáticamente un email de invitación al técnico

> ⚠️ **Importante:** El técnico debe **aceptar la invitación** y crear su contraseña antes de poder ingresar al portal.

### ¿Por qué no aparece en el campo "Técnico" de la orden?

El campo técnico muestra usuarios **activos** (internos y de portal). Si no aparece:
- El usuario todavía no aceptó la invitación → su cuenta no está activa
- El usuario fue archivado → buscarlo con el filtro "Archivados" y reactivarlo
- Aún no fue creado → seguir los pasos de arriba

---

## 4. Crear una Orden de Servicio

Ir a **Servicios en Campo → Mis Órdenes → Nuevo** (o botón "+" en Kanban).

### Campos obligatorios

| Campo | Descripción |
|-------|-------------|
| **Tipo de Servicio** | Reparación / Instalación / Mantenimiento / Inspección / Otro |
| **Cliente** | Contacto del cliente (Many2one a Contactos) |

### Campos recomendados

| Campo | Descripción |
|-------|-------------|
| **Prioridad** | Normal o Urgente (estrella) |
| **Dirección del Servicio** | Si difiere de la dirección del cliente |
| **Orden de Venta** | Vincula con una OV existente (opcional) |
| **Responsable** | Usuario interno que gestiona la orden |
| **Técnico** | Quien realiza el trabajo (interno o portal) |
| **Fecha Programada** | Cuándo se realizará el servicio |
| **Descripción del Trabajo** | Detalle de lo que se debe hacer |

### Numeración automática
La orden se guarda con número **FSO/AAAA/NNNNN** (ej: FSO/2025/00001). Se genera al guardar.

---

## 5. Flujo de estados

```
BORRADOR → ASIGNADO → EN CURSO → COMPLETADO → FACTURADO/COBRADO
                ↘________________↗
                     CANCELADO  ←→  BORRADOR (restablecido)
```

### Botones y condiciones

| Botón | Desde | Resultado | Condición |
|-------|-------|-----------|-----------|
| **Asignar a Técnico** | Borrador | → Asignado | Requiere técnico asignado |
| **Iniciar** | Borrador / Asignado | → En Curso | Registra hora de inicio |
| **Marcar como Completado** | En Curso | → Completado | Registra hora de finalización |
| **Cerrar / Cobrado** | Completado | → Facturado | Genera recibo si hay pagos |
| **Cancelar** | Cualquiera excepto Facturado | → Cancelado | — |
| **Restablecer** | Cancelado | → Borrador | — |

### Acciones adicionales (header)

| Botón | Cuándo aparece | Qué hace |
|-------|----------------|----------|
| **Enviar Link al Técnico** | Asignado / En Curso | Envía email al técnico con link al portal |
| **Capturar Firma** | En Curso / Completado | Abre wizard para firmar |

---

## 6. Registrar materiales y horas

### Pestaña "Materiales y Servicios"

Aquí se registran los **productos y servicios utilizados** en la orden.

1. Hacer clic en **"Agregar una línea"**
2. Seleccionar el **Producto** (muestra solo productos habilitados para venta)
3. Ajustar:
   - **Cantidad** (por defecto 1)
   - **Unidad** (se completa automáticamente desde el producto)
   - **Precio Unitario** (se completa desde el precio estándar o lista de precios)
   - **Impuestos** (se completa automáticamente desde el producto)
4. El **Subtotal** y **Total** se calculan solos

Al pie de la tabla aparece el resumen:
- **Base Imponible** · **Impuestos** · **Total** · **Pagado** · **Saldo Pendiente**

> 💡 Para registrar **horas de trabajo** como línea: crear un producto de tipo "Servicio" llamado "Hora de Trabajo" con precio unitario = tarifa/hora, y agregarlo como línea con la cantidad de horas.

### Campo "Horas Trabajadas"

En el grupo **"Responsables y Fechas"** del formulario hay un campo **Horas Trabajadas** donde se puede registrar directamente las horas totales insumidas en la visita (independientemente de las líneas).

---

## 7. Registrar pagos en campo

### Pestaña "Pagos en Campo"

Permite registrar cobros realizados durante la visita (efectivo, tarjeta, transferencia, etc.).

**Para agregar un pago:**
1. Hacer clic en **"Agregar una línea"** en la pestaña Pagos
2. Completar:
   - **Fecha** (por defecto hoy)
   - **Método de pago**: Efectivo / Tarjeta Crédito / Tarjeta Débito / Transferencia / Cheque / Otro
   - **Importe**
   - **Referencia** (número de transacción, autorización, etc.)
3. El pago queda en estado **"Registrado"**

**Estados del pago:**

| Estado | Significado |
|--------|-------------|
| **Registrado** | Cargado pero no confirmado |
| **Confirmado** | Confirmado — se suma al total cobrado |
| **Cancelado** | Anulado |

**Para confirmar:** usar el botón **"Confirmar"** en la línea del pago.

**Para registrar en contabilidad:** una vez confirmado, aparece el botón **"Registrar en Cont."** que crea el pago contable vinculado.

> El **Saldo Pendiente** se calcula automáticamente: Total − Pagos Confirmados.

---

## 8. Capturar la firma del cliente

El botón **"Capturar Firma"** aparece cuando la orden está **En Curso** o **Completada**.

1. Hacer clic en **"Capturar Firma"**
2. Se abre un wizard con:
   - Nombre de la orden y cliente (readonly)
   - **Texto de conformidad** (editable si se necesita personalizar)
   - **Nombre del firmante** (quién firma en nombre del cliente)
   - **Canvas de firma** — el cliente dibuja su firma con mouse o pantalla táctil
3. Hacer clic en **"Guardar Firma"**

La firma queda guardada en la orden y es visible:
- En la pestaña **"Firma del Cliente"**
- En el encabezado del formulario (miniatura)
- En el **Recibo PDF**

---

## 9. Reportes e impresión

### Smart Buttons (parte superior del formulario)

| Botón | Cuándo aparece | Contenido |
|-------|----------------|-----------|
| **Planilla** 🖨️ | Siempre | Hoja de trabajo completa: datos, descripción, materiales, notas del técnico, sección de firmas |
| **Recibo** 📄 | Si tiene N° de recibo | Recibo de pago: detalle de servicios, pagos recibidos, firma |
| **Orden Venta** 🛒 | Si tiene OV vinculada | Abre la Orden de Venta en Odoo |

### ¿Cuándo se genera el N° de Recibo?
Al presionar **"Cerrar / Cobrado"**, si la orden tiene al menos un pago confirmado, se genera automáticamente el número **REC/AAAA/NNNNN**.

---

## 10. Portal del técnico (acceso externo)

Los técnicos de portal acceden desde **`https://[tu-dominio]/my/field-service`**

### Lo que ve el técnico

1. **Lista de sus órdenes** con filtros: Todas / Asignadas / En Curso / Completadas
2. Al entrar a una orden, ve:

#### Columna izquierda
- **Datos del cliente** (nombre, teléfono, email, dirección)
- **Descripción del trabajo** a realizar
- **Materiales y Servicios**: puede agregar/eliminar líneas de productos
- **Mis Notas**: puede escribir y guardar notas del técnico

#### Columna derecha
- **Información** (tipo, responsable, fechas, estado)
- **Cobros registrados**: puede registrar pagos directamente desde el portal
- **Firma del cliente**: puede capturar la firma desde el portal (canvas táctil)

### Acciones que puede hacer el técnico

| Acción | Condición |
|--------|-----------|
| **Iniciar Trabajo** | Si la orden está en Borrador o Asignada |
| **Marcar como Completado** | Si la orden está En Curso |
| **Agregar materiales** | Si está En Curso o Completada |
| **Registrar cobro** | Si está En Curso o Completada |
| **Capturar firma** | Si está En Curso o Completada |
| **Descargar Recibo** | Si tiene número de recibo |

> El técnico **no puede** ver notas internas, ni modificar datos del cliente, ni cancelar la orden.

### Cómo enviar el link al técnico

Desde la orden, con estado **Asignado** o **En Curso**:
- Botón **"Enviar Link al Técnico"** → envía email automático con el link directo a esa orden

O el técnico puede entrar directamente a `/my/field-service` y ver todas sus órdenes asignadas.

---

## 11. Preguntas frecuentes

**¿Por qué no encuentro al técnico en el campo "Técnico"?**
El técnico debe existir como usuario en Odoo (interno o portal) y su cuenta debe estar activa (debe haber aceptado la invitación). Ver [sección 3](#3-crear-un-técnico-usuario-de-portal).

**¿Puedo asignar un técnico interno como técnico de campo?**
Sí. Cualquier usuario activo de Odoo (interno o portal) puede ser asignado como técnico.

**¿El técnico de portal consume licencia?**
No. Los usuarios de portal en Odoo.com son gratuitos e ilimitados.

**¿Se puede vincular con una Orden de Venta existente?**
Sí. Al vincular una OV, al cerrar la orden se sincronizan automáticamente las líneas de materiales a la OV para su facturación.

**¿Se puede imprimir la planilla antes de que la orden esté completada?**
Sí. El botón "Planilla" está siempre disponible en cualquier estado.

**¿Qué pasa si el técnico no tiene email?**
El botón "Enviar Link" arrojará un error. El técnico necesita email válido para recibir notificaciones.

**¿Puedo tener múltiples técnicos por orden?**
No. El módulo actual soporta un único técnico por orden.

---

*Módulo desarrollado por Econovex · Odoo 19*
