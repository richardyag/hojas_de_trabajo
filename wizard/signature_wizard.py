# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FsoSignatureWizard(models.TransientModel):
    """Wizard para capturar firma del cliente desde el backend."""
    _name = 'fso.signature.wizard'
    _description = 'Captura de Firma del Cliente'

    order_id = fields.Many2one(
        'field.service.order', string='Orden', required=True, ondelete='cascade'
    )
    order_name = fields.Char(related='order_id.name', string='Orden Ref.')
    partner_name = fields.Char(related='order_id.partner_id.name', string='Cliente')

    signed_by = fields.Char(
        string='Nombre del Firmante', required=True,
        help='Nombre de la persona que firma en representación del cliente'
    )
    signature = fields.Binary(
        string='Firma', required=True,
        help='Dibuje la firma del cliente en el recuadro'
    )
    # Texto legal configurable
    signature_text = fields.Html(
        string='Texto Legal',
        default=lambda self: _(
            '<p>Al firmar confirmo que el trabajo descrito en esta orden de '
            'servicio fue realizado a mi conformidad y acepto los términos '
            'del servicio prestado.</p>'
        )
    )

    def action_sign(self):
        self.ensure_one()
        if not self.signature:
            raise UserError(_('Debe capturar la firma antes de confirmar.'))
        self.order_id.write({
            'signature': self.signature,
            'signed_by': self.signed_by,
            'signed_on': fields.Datetime.now(),
        })
        self.order_id.message_post(
            body=_('Orden firmada por <b>%s</b>.') % self.signed_by,
            subtype_xmlid='mail.mt_note',
        )
        return {'type': 'ir.actions.act_window_close'}
