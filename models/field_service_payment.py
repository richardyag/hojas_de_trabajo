# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FieldServicePayment(models.Model):
    _name = 'field.service.payment'
    _description = 'Pago Registrado en Campo'
    _order = 'date desc, id desc'

    order_id = fields.Many2one(
        'field.service.order', string='Orden', required=True,
        ondelete='cascade', index=True
    )
    name = fields.Char(
        string='Referencia',
        compute='_compute_name', store=True
    )
    date = fields.Date(
        string='Fecha', required=True,
        default=fields.Date.today
    )
    payment_method = fields.Selection([
        ('cash',          'Efectivo'),
        ('credit_card',   'Tarjeta de Crédito'),
        ('debit_card',    'Tarjeta de Débito'),
        ('transfer',      'Transferencia Bancaria'),
        ('check',         'Cheque'),
        ('other',         'Otro'),
    ], string='Método de Pago', required=True, default='cash')

    amount = fields.Monetary(
        string='Importe', required=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id', string='Moneda', store=True
    )

    reference = fields.Char(
        string='Referencia / N° Comprobante',
        help='Número de transacción, autorización de tarjeta, etc.'
    )
    notes = fields.Text(string='Notas')

    state = fields.Selection([
        ('draft', 'Registrado'),
        ('done',  'Confirmado'),
        ('cancel', 'Cancelado'),
    ], default='draft', string='Estado', tracking=True)

    # Vínculo opcional con cuenta contable
    account_payment_id = fields.Many2one(
        'account.payment', string='Pago Contable',
        readonly=True, copy=False,
        help='Pago contable generado automáticamente (si aplica)'
    )

    receipt_number = fields.Char(
        related='order_id.receipt_number', string='N° Recibo', readonly=True
    )

    # ──────────────────────────────────────────────────────────────────────────
    @api.depends('payment_method', 'amount', 'order_id.name')
    def _compute_name(self):
        method_labels = dict(
            self._fields['payment_method'].selection
        )
        for pay in self:
            method = method_labels.get(pay.payment_method, '')
            pay.name = '%s – %s – %s' % (
                pay.order_id.name or '',
                method,
                pay.amount,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Acciones de estado
    # ──────────────────────────────────────────────────────────────────────────

    def action_confirm(self):
        for pay in self:
            pay.write({'state': 'done'})
        # Recalcular montos en la orden
        self.mapped('order_id')._compute_amounts()

    def action_cancel(self):
        for pay in self:
            if pay.account_payment_id:
                raise UserError(
                    _('No se puede cancelar un pago ya registrado en contabilidad.')
                )
            pay.write({'state': 'cancel'})
        self.mapped('order_id')._compute_amounts()

    def action_reset_draft(self):
        self.filtered(lambda p: p.state == 'cancel').write({'state': 'draft'})

    def action_create_account_payment(self):
        """Crea un pago contable (account.payment) vinculado."""
        self.ensure_one()
        if self.account_payment_id:
            raise UserError(_('Ya existe un pago contable asociado.'))
        if self.state != 'done':
            raise UserError(_('Confirme el pago antes de registrarlo en contabilidad.'))

        order = self.order_id
        journal = self.env['account.journal'].search([
            ('type', 'in', ['cash', 'bank']),
            ('company_id', '=', order.company_id.id),
        ], limit=1)

        if not journal:
            raise UserError(_('No se encontró un diario de efectivo/banco configurado.'))

        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': order.partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': journal.id,
            'ref': '%s – %s' % (order.name, self.reference or ''),
            'company_id': order.company_id.id,
        }
        payment = self.env['account.payment'].create(payment_vals)
        self.account_payment_id = payment.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }
