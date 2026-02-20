# -*- coding: utf-8 -*-
from odoo import models, fields


class FsoChecklistTemplate(models.Model):
    """Plantilla reutilizable de checklist para órdenes de servicio."""
    _name = 'fso.checklist.template'
    _description = 'Plantilla de Checklist'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many(
        'fso.checklist.template.line', 'template_id',
        string='Ítems'
    )


class FsoChecklistTemplateLine(models.Model):
    """Ítem de una plantilla de checklist."""
    _name = 'fso.checklist.template.line'
    _description = 'Ítem de Plantilla de Checklist'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'fso.checklist.template', string='Plantilla',
        ondelete='cascade', required=True
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Descripción', required=True)


class FsoChecklistItem(models.Model):
    """Ítem de checklist vinculado a una orden de servicio concreta."""
    _name = 'fso.checklist.item'
    _description = 'Ítem de Checklist'
    _order = 'sequence, id'

    order_id = fields.Many2one(
        'field.service.order', string='Orden',
        ondelete='cascade', required=True
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string='Descripción', required=True, readonly=True)
    is_done = fields.Boolean(string='Completado')
    notes = fields.Text(string='Observaciones')
