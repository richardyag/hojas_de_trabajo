# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FieldServiceLine(models.Model):
    _name = 'field.service.line'
    _description = 'Línea de Orden de Servicio'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'field.service.order', string='Orden', required=True,
        ondelete='cascade', index=True
    )
    sequence = fields.Integer(default=10)

    product_id = fields.Many2one(
        'product.product', string='Producto / Servicio',
        domain=[('sale_ok', '=', True)],
        change_default=True, ondelete='restrict'
    )
    description = fields.Text(
        string='Descripción',
        compute='_compute_description', store=True, readonly=False
    )

    qty = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        default=1.0
    )
    product_uom_id = fields.Many2one(
        'uom.uom', string='Unidad',
        compute='_compute_product_uom', store=True, readonly=False
    )

    price_unit = fields.Float(
        string='Precio Unit.',
        digits='Product Price',
        compute='_compute_price_unit', store=True, readonly=False
    )

    tax_ids = fields.Many2many(
        'account.tax', string='Impuestos',
        compute='_compute_tax_ids', store=True, readonly=False,
        domain=[('type_tax_use', '=', 'sale')]
    )

    price_subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_amounts', store=True,
        currency_field='currency_id'
    )
    price_tax = fields.Monetary(
        string='Impuesto', compute='_compute_amounts', store=True,
        currency_field='currency_id'
    )
    price_total = fields.Monetary(
        string='Total c/imp.', compute='_compute_amounts', store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        related='order_id.currency_id', string='Moneda', store=True
    )

    # Vínculo con Sale Order Line (cuando se sincroniza)
    sale_order_line_id = fields.Many2one(
        'sale.order.line', string='Línea de Venta',
        readonly=True, copy=False
    )

    # ──────────────────────────────────────────────────────────────────────────
    # Cómputos
    # ──────────────────────────────────────────────────────────────────────────

    @api.depends('product_id')
    def _compute_description(self):
        for line in self:
            if line.product_id:
                lang = line.order_id.partner_id.lang or self.env.lang
                product = line.product_id.with_context(lang=lang)
                line.description = (
                    product.description_sale or product.name or ''
                )
            elif not line.description:
                line.description = ''

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            line.product_uom_id = (
                line.product_id.uom_id if line.product_id else False
            )

    @api.depends('product_id', 'order_id.partner_id', 'qty')
    def _compute_price_unit(self):
        for line in self:
            if not line.product_id:
                line.price_unit = 0.0
                continue
            # Intentar usar la lista de precios de la orden de venta vinculada
            pricelist = (
                line.order_id.sale_order_id.pricelist_id
                if line.order_id.sale_order_id
                else False
            )
            if pricelist:
                try:
                    # API Odoo 17+
                    line.price_unit = pricelist._get_product_price(
                        line.product_id,
                        line.qty or 1.0,
                        currency=line.currency_id,
                    )
                except Exception:
                    line.price_unit = line.product_id.lst_price
            else:
                line.price_unit = line.product_id.lst_price

    @api.depends('product_id', 'order_id.company_id')
    def _compute_tax_ids(self):
        for line in self:
            if line.product_id:
                line.tax_ids = line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == line.order_id.company_id
                )
            else:
                line.tax_ids = False

    @api.depends('qty', 'price_unit', 'tax_ids')
    def _compute_amounts(self):
        for line in self:
            price = line.price_unit * line.qty
            taxes = line.tax_ids.compute_all(
                price, currency=line.currency_id,
                quantity=1.0,
                product=line.product_id,
                partner=line.order_id.partner_id,
            )
            line.price_subtotal = taxes['total_excluded']
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
            line.price_total = taxes['total_included']
