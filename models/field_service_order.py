# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


class FieldServiceOrder(models.Model):
    _name = 'field.service.order'
    _description = 'Orden de Servicio en Campo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'scheduled_date desc, id desc'

    # ─── Identificación ────────────────────────────────────────────────────────
    name = fields.Char(
        string='Referencia', readonly=True, default='Nuevo',
        copy=False, tracking=True
    )
    state = fields.Selection([
        ('draft',      'Borrador'),
        ('assigned',   'Asignado'),
        ('in_progress', 'En Curso'),
        ('done',       'Completado'),
        ('invoiced',   'Facturado / Cobrado'),
        ('cancelled',  'Cancelado'),
    ], default='draft', string='Estado', tracking=True, copy=False,
       group_expand='_group_expand_states')

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgente'),
    ], default='0', string='Prioridad')

    service_type = fields.Selection([
        ('repair',       'Reparación'),
        ('installation', 'Instalación'),
        ('maintenance',  'Mantenimiento'),
        ('inspection',   'Inspección'),
        ('other',        'Otro'),
    ], string='Tipo de Servicio', required=True, default='repair', tracking=True)

    # ─── Partes ────────────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', required=True,
        tracking=True, index=True
    )
    partner_phone = fields.Char(
        related='partner_id.phone', string='Teléfono', readonly=True
    )
    partner_email = fields.Char(
        related='partner_id.email', string='Email', readonly=True
    )
    partner_street = fields.Char(
        related='partner_id.street', string='Calle', readonly=True
    )
    partner_city = fields.Char(
        related='partner_id.city', string='Ciudad', readonly=True
    )

    service_address_id = fields.Many2one(
        'res.partner', string='Dirección del Servicio',
        domain="['|', ('id', '=', partner_id), ('parent_id', '=', partner_id)]",
        help='Dirección donde se realizará el servicio (si difiere del cliente)'
    )

    # ─── Responsables ─────────────────────────────────────────────────────────
    user_id = fields.Many2one(
        'res.users', string='Responsable',
        default=lambda self: self.env.user,
        tracking=True, domain=[('share', '=', False)]
    )
    technician_id = fields.Many2one(
        'res.users', string='Técnico', tracking=True,
        help='Puede ser usuario interno o de portal (sin costo de licencia adicional)'
    )
    technician_partner_id = fields.Many2one(
        related='technician_id.partner_id', string='Contacto Técnico', readonly=True
    )

    # ─── Fechas ────────────────────────────────────────────────────────────────
    scheduled_date = fields.Datetime(string='Fecha Programada', tracking=True)
    start_date = fields.Datetime(string='Inicio Real', readonly=True, copy=False)
    completion_date = fields.Datetime(string='Finalización', readonly=True, copy=False)

    # ─── Vinculación comercial ────────────────────────────────────────────────
    sale_order_id = fields.Many2one(
        'sale.order', string='Orden de Venta',
        domain="[('partner_id', 'child_of', partner_id), ('state', 'in', ['sale','done'])]",
        tracking=True,
        help='Vincule con una Orden de Venta para sincronizar líneas y facturación'
    )
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        related='company_id.currency_id', readonly=True
    )
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        default=lambda self: self.env.company, required=True
    )

    # ─── Descripción ──────────────────────────────────────────────────────────
    description = fields.Html(
        string='Descripción / Trabajo a Realizar',
        help='Descripción detallada del trabajo solicitado'
    )
    technician_notes = fields.Text(
        string='Notas del Técnico',
        help='Observaciones registradas por el técnico durante la visita'
    )
    internal_notes = fields.Html(
        string='Notas Internas',
        help='Información interna, no visible en el portal ni en el recibo'
    )

    # ─── Líneas y pagos ───────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'field.service.line', 'order_id',
        string='Materiales y Servicios'
    )
    payment_ids = fields.One2many(
        'field.service.payment', 'order_id',
        string='Pagos'
    )

    # ─── Firma ────────────────────────────────────────────────────────────────
    signature = fields.Binary(
        string='Firma del Cliente', copy=False, attachment=True
    )
    signed_by = fields.Char(string='Firmado por', copy=False, tracking=True)
    signed_on = fields.Datetime(string='Fecha de Firma', copy=False)

    # ─── Montos calculados ────────────────────────────────────────────────────
    amount_untaxed = fields.Monetary(
        compute='_compute_amounts', string='Base Imponible',
        store=True, tracking=True
    )
    amount_tax = fields.Monetary(
        compute='_compute_amounts', string='Impuestos', store=True
    )
    amount_total = fields.Monetary(
        compute='_compute_amounts', string='Total', store=True, tracking=True
    )
    amount_paid = fields.Monetary(
        compute='_compute_amounts', string='Pagado', store=True
    )
    amount_due = fields.Monetary(
        compute='_compute_amounts', string='Saldo Pendiente', store=True
    )

    # ─── Recibo ───────────────────────────────────────────────────────────────
    receipt_number = fields.Char(
        string='N° Recibo', copy=False, readonly=True, tracking=True
    )

    # ──────────────────────────────────────────────────────────────────────────
    # ORM
    # ──────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('field.service.order')
                    or 'Nuevo'
                )
        return super().create(vals_list)

    def _compute_access_url(self):
        super()._compute_access_url()
        for order in self:
            order.access_url = '/my/field-service/%s' % order.id

    # ──────────────────────────────────────────────────────────────────────────
    # Cómputos
    # ──────────────────────────────────────────────────────────────────────────

    @api.depends(
        'line_ids.price_subtotal', 'line_ids.price_tax',
        'payment_ids.amount', 'payment_ids.state'
    )
    def _compute_amounts(self):
        for order in self:
            order.amount_untaxed = sum(order.line_ids.mapped('price_subtotal'))
            order.amount_tax = sum(order.line_ids.mapped('price_tax'))
            order.amount_total = order.amount_untaxed + order.amount_tax
            order.amount_paid = sum(
                p.amount for p in order.payment_ids
                if p.state == 'done'
            )
            order.amount_due = order.amount_total - order.amount_paid

    @api.model
    def _group_expand_states(self, states, domain, order):
        return [key for key, _val in self._fields['state'].selection]

    # ──────────────────────────────────────────────────────────────────────────
    # Máquina de estados
    # ──────────────────────────────────────────────────────────────────────────

    def button_assign(self):
        for order in self:
            if not order.technician_id:
                raise UserError(
                    _('Debe asignar un técnico antes de confirmar la orden.')
                )
            order.write({'state': 'assigned'})
            order._notify_technician()

    def button_start(self):
        for order in self:
            if order.state not in ('assigned', 'draft'):
                raise UserError(_('Solo se puede iniciar una orden asignada.'))
            order.write({
                'state': 'in_progress',
                'start_date': fields.Datetime.now(),
            })

    def button_done(self):
        for order in self:
            if order.state != 'in_progress':
                raise UserError(_('La orden debe estar en curso para completarla.'))
            order.write({
                'state': 'done',
                'completion_date': fields.Datetime.now(),
            })

    def button_invoice(self):
        """Marcar como facturado/cobrado y generar recibo si aplica."""
        for order in self:
            if order.sale_order_id:
                order._sync_lines_to_sale_order()
            if order.payment_ids.filtered(lambda p: p.state == 'done'):
                order._generate_receipt_number()
            order.write({'state': 'invoiced'})

    def button_cancel(self):
        for order in self:
            if order.state == 'invoiced':
                raise UserError(_('No se puede cancelar una orden ya facturada/cobrada.'))
        self.write({'state': 'cancelled'})

    def button_reset(self):
        self.filtered(lambda o: o.state == 'cancelled').write({'state': 'draft'})

    # ──────────────────────────────────────────────────────────────────────────
    # Acciones
    # ──────────────────────────────────────────────────────────────────────────

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    def action_send_portal_link(self):
        """Envía al técnico el link de acceso al portal."""
        self.ensure_one()
        if not self.technician_id:
            raise UserError(_('No hay técnico asignado.'))
        if not self.technician_id.partner_id.email:
            raise UserError(_('El técnico no tiene email configurado.'))
        template = self.env.ref(
            'hojas_de_trabajo.mail_template_fso_portal_link',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)
        else:
            url = self.access_url
            self.message_post(
                body=_(
                    'Accede a tu Orden de Servicio: '
                    '<a href="%(url)s">%(name)s</a>',
                    url=url, name=self.name
                ),
                partner_ids=[self.technician_id.partner_id.id],
                subtype_xmlid='mail.mt_comment',
            )
        return {'type': 'ir.actions.act_window_close'}

    def action_print_receipt(self):
        self.ensure_one()
        return self.env.ref(
            'hojas_de_trabajo.action_report_fso_receipt'
        ).report_action(self)

    def action_print_workorder(self):
        self.ensure_one()
        return self.env.ref(
            'hojas_de_trabajo.action_report_fso_workorder'
        ).report_action(self)

    def action_open_signature_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Capturar Firma del Cliente'),
            'res_model': 'fso.signature.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers privados
    # ──────────────────────────────────────────────────────────────────────────

    def _notify_technician(self):
        """Notifica al técnico cuando se le asigna la orden."""
        for order in self:
            if order.technician_id and order.technician_id.partner_id:
                body = _(
                    'Hola <b>%(tech)s</b>, se te ha asignado la orden de servicio '
                    '<b>%(name)s</b> para el cliente <b>%(partner)s</b>.<br/>'
                    'Fecha programada: <b>%(date)s</b>.<br/>'
                    '<a href="%(url)s">Acceder a la orden</a>',
                    tech=order.technician_id.name,
                    name=order.name,
                    partner=order.partner_id.name,
                    date=order.scheduled_date or 'Por definir',
                    url=order.access_url,
                )
                order.message_post(
                    body=body,
                    partner_ids=[order.technician_id.partner_id.id],
                    subtype_xmlid='mail.mt_comment',
                    email_layout_xmlid='mail.mail_notification_light',
                )

    def _sync_lines_to_sale_order(self):
        """Agrega las líneas de campo que aún no existen en la orden de venta."""
        SaleLine = self.env['sale.order.line']
        for order in self:
            if not order.sale_order_id:
                continue
            for line in order.line_ids.filtered(lambda l: not l.sale_order_line_id):
                sol = SaleLine.create({
                    'order_id': order.sale_order_id.id,
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.name,
                    'product_uom_qty': line.qty,
                    'price_unit': line.price_unit,
                    'tax_id': line.tax_ids.ids,
                })
                line.sale_order_line_id = sol.id

    def _generate_receipt_number(self):
        """Genera número de recibo si no tiene uno."""
        for order in self:
            if not order.receipt_number:
                order.receipt_number = (
                    self.env['ir.sequence'].next_by_code('field.service.receipt')
                    or '/'
                )
