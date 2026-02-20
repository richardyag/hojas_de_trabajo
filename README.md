# Field Service – Hojas de Trabajo

Módulo de **gestión de servicios en campo** para **Odoo 19**, desarrollado por [Econovex](https://www.econovex.com).

## Características principales

- **Órdenes de Servicio (FSO):** creación, asignación y seguimiento completo
- **Técnicos como usuarios de portal:** sin costo de licencia interna adicional
- **Portal web para técnicos:** gestión completa de la planilla desde cualquier dispositivo
- **Materiales y servicios:** registro con búsqueda de productos en tiempo real (AJAX)
- **Cobro en campo:** efectivo, tarjeta de crédito/débito, transferencia y más
- **Recibo PDF:** generado automáticamente al registrar el cobro
- **Firma digital del cliente:** captura en canvas táctil/mouse, lista para Odoo Sign
- **Integración con Órdenes de Venta:** sincronización de líneas y facturación
- **Integración contable:** creación opcional de `account.payment` desde el módulo
- **Notificaciones:** email automático al técnico con link de acceso al portal

## Flujo de trabajo

```
Responsable (backend)           Técnico (portal /my/field-service)
       │                                    │
  Crea la FSO                               │
  Asigna técnico  ──── email + link ──────► │
  (usuario portal)                     Ve la orden
       │                               Inicia el trabajo
       │                               Registra materiales
       │                               Anota observaciones
       │                               Registra cobro
       │                               Captura firma del cliente
       │                               Marca como completado
       │ ◄──────── notificación ────────────│
  Revisa y cierra
  Sincroniza con OV
  Genera pago contable
```

## Modelos

| Modelo | Descripción |
|--------|-------------|
| `field.service.order` | Orden de servicio principal |
| `field.service.line` | Líneas de productos/servicios utilizados |
| `field.service.payment` | Pagos registrados en campo |
| `fso.signature.wizard` | Wizard de firma (backend) |

## Estados de la Orden

`Borrador` → `Asignado` → `En Curso` → `Completado` → `Facturado/Cobrado`

## Grupos de seguridad

| Grupo | Permisos |
|-------|----------|
| Gerente de Servicios | Acceso total a todos los registros |
| Usuario de Servicios | Ve sus propias órdenes y las asignadas |
| Portal (Técnico) | Solo ve sus órdenes asignadas (vía portal) |

## Instalación

1. Copiar la carpeta `hojas_de_trabajo` al directorio de addons de Odoo
2. Actualizar la lista de módulos: `Settings > Activate developer mode > Update Apps List`
3. Buscar **"Field Service – Hojas de Trabajo"** e instalar

## Dependencias

```python
depends = ['base', 'mail', 'portal', 'sale_management', 'account', 'product', 'web']
```

## Compatibilidad

- **Odoo 19** (Community / Enterprise)

## Licencia

LGPL-3 — ver [LICENSE](https://www.gnu.org/licenses/lgpl-3.0.html)

---

Desarrollado por **Econovex** · [econovex.com](https://www.econovex.com)
