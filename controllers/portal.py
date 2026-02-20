# -*- coding: utf-8 -*-
import base64
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class FieldServicePortal(CustomerPortal):
    """Controlador portal para técnicos (usuarios de portal)."""

    # ──────────────────────────────────────────────────────────────────────────
    # Home portal: contador
    # ──────────────────────────────────────────────────────────────────────────

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'fso_count' in counters:
            domain = self._get_fso_domain()
            values['fso_count'] = (
                request.env['field.service.order'].search_count(domain)
            )
        return values

    def _get_fso_domain(self):
        return [('technician_id', '=', request.env.user.id)]

    # ──────────────────────────────────────────────────────────────────────────
    # Lista de órdenes
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        ['/my/field-service', '/my/field-service/page/<int:page>'],
        type='http', auth='user', website=True
    )
    def portal_my_field_service(self, page=1, sortby=None, filterby=None, **kw):
        domain = self._get_fso_domain()
        FSO = request.env['field.service.order']

        searchbar_sortings = {
            'date':  {'label': _('Fecha programada'), 'order': 'scheduled_date desc'},
            'name':  {'label': _('Referencia'),        'order': 'name'},
            'state': {'label': _('Estado'),            'order': 'state'},
        }
        searchbar_filters = {
            'all':         {'label': _('Todas'),         'domain': []},
            'assigned':    {'label': _('Asignadas'),     'domain': [('state', '=', 'assigned')]},
            'in_progress': {'label': _('En Curso'),      'domain': [('state', '=', 'in_progress')]},
            'done':        {'label': _('Completadas'),   'domain': [('state', '=', 'done')]},
        }

        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'

        order = searchbar_sortings[sortby]['order']
        domain += searchbar_filters[filterby]['domain']

        order_count = FSO.search_count(domain)
        pager = portal_pager(
            url='/my/field-service',
            url_args={'sortby': sortby, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page,
        )

        orders = FSO.search(domain, order=order, limit=self._items_per_page,
                            offset=pager['offset'])

        return request.render('hojas_de_trabajo.portal_fso_list', {
            'orders': orders,
            'page_name': 'field_service',
            'pager': pager,
            'default_url': '/my/field-service',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
        })

    # ──────────────────────────────────────────────────────────────────────────
    # Detalle de orden
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        ['/my/field-service/<int:order_id>'],
        type='http', auth='user', website=True
    )
    def portal_fso_detail(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        products = request.env['product.product'].sudo().search([
            ('sale_ok', '=', True)
        ], limit=200, order='name')
        taxes = request.env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', order_sudo.company_id.id),
        ])
        return request.render('hojas_de_trabajo.portal_fso_detail', {
            'order': order_sudo,
            'page_name': 'field_service',
            'products': products,
            'taxes': taxes,
            'error': kw.get('error', ''),
            'success': kw.get('success', ''),
        })

    # ──────────────────────────────────────────────────────────────────────────
    # Acciones de estado
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/start',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_start(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)
        if order_sudo.state in ('draft', 'assigned'):
            order_sudo.sudo().button_start()
        return request.redirect('/my/field-service/%s' % order_id)

    @http.route(
        '/my/field-service/<int:order_id>/done',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_done(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)
        if order_sudo.state == 'in_progress':
            order_sudo.sudo().button_done()
        return request.redirect('/my/field-service/%s' % order_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Gestión de líneas (materiales usados)
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/add-line',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_add_line(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)

        product_id = int(kw.get('product_id', 0))
        qty = float(kw.get('qty', 1.0))
        price_unit = float(kw.get('price_unit', 0.0))
        description = kw.get('description', '')
        tax_ids_raw = kw.get('tax_ids', '')

        if not product_id:
            return request.redirect(
                '/my/field-service/%s?error=Debe seleccionar un producto' % order_id
            )

        product = request.env['product.product'].sudo().browse(product_id)
        if not product.exists():
            return request.redirect(
                '/my/field-service/%s?error=Producto no encontrado' % order_id
            )

        # Calcular precio si no viene
        if not price_unit:
            price_unit = product.lst_price

        # Impuestos
        tax_ids = []
        if tax_ids_raw:
            try:
                tax_ids = [int(t) for t in tax_ids_raw.split(',') if t.strip()]
            except ValueError:
                pass
        if not tax_ids:
            company = order_sudo.company_id
            tax_ids = product.taxes_id.filtered(
                lambda t: t.company_id == company
            ).ids

        line_vals = {
            'order_id': order_sudo.id,
            'product_id': product.id,
            'description': description or product.name,
            'qty': qty,
            'price_unit': price_unit,
            'tax_ids': [(6, 0, tax_ids)],
        }
        request.env['field.service.line'].sudo().create(line_vals)
        return request.redirect('/my/field-service/%s' % order_id)

    @http.route(
        '/my/field-service/<int:order_id>/remove-line/<int:line_id>',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_remove_line(self, order_id, line_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)
        line = request.env['field.service.line'].sudo().browse(line_id)
        if line.exists() and line.order_id.id == order_sudo.id:
            if not line.sale_order_line_id:
                line.unlink()
        return request.redirect('/my/field-service/%s' % order_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Notas del técnico
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/notes',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_notes(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)
        notes = kw.get('technician_notes', '')
        order_sudo.sudo().write({'technician_notes': notes})
        return request.redirect('/my/field-service/%s' % order_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Firma del cliente
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/sign',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_sign(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)

        signature_data = kw.get('signature', '')
        signed_by = kw.get('signed_by', '').strip()

        if not signature_data or not signed_by:
            return request.redirect(
                '/my/field-service/%s?error=Complete el nombre y la firma' % order_id
            )

        # Limpiar prefijo data URL si viene del canvas
        if ',' in signature_data:
            signature_data = signature_data.split(',', 1)[1]

        try:
            sig_bytes = base64.b64decode(signature_data)
        except Exception:
            return request.redirect(
                '/my/field-service/%s?error=Firma inválida' % order_id
            )

        from odoo import fields as F
        order_sudo.sudo().write({
            'signature': base64.b64encode(sig_bytes),
            'signed_by': signed_by,
            'signed_on': F.Datetime.now(),
        })
        order_sudo.sudo().message_post(
            body=_('Orden firmada digitalmente por <b>%s</b> desde el portal.') % signed_by,
            subtype_xmlid='mail.mt_note',
        )
        return request.redirect(
            '/my/field-service/%s?success=Firma registrada correctamente' % order_id
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Registro de pago en campo
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/payment',
        type='http', auth='user', website=True, methods=['POST']
    )
    def portal_fso_payment(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        self._check_is_technician(order_sudo)

        method = kw.get('payment_method', 'cash')
        reference = kw.get('reference', '')
        notes = kw.get('notes', '')
        try:
            amount = float(kw.get('amount', 0.0))
        except (ValueError, TypeError):
            return request.redirect(
                '/my/field-service/%s?error=Importe inválido' % order_id
            )

        if amount <= 0:
            return request.redirect(
                '/my/field-service/%s?error=El importe debe ser mayor a cero' % order_id
            )

        pay = request.env['field.service.payment'].sudo().create({
            'order_id': order_sudo.id,
            'payment_method': method,
            'amount': amount,
            'reference': reference,
            'notes': notes,
            'state': 'done',
        })
        order_sudo.sudo()._generate_receipt_number()
        return request.redirect(
            '/my/field-service/%s?success=Pago registrado correctamente' % order_id
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Búsqueda de productos (JSON)
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/products/search',
        type='json', auth='user', website=True
    )
    def portal_product_search(self, query='', **kw):
        if len(query) < 2:
            return {'products': []}
        products = request.env['product.product'].sudo().search([
            '|',
            ('name', 'ilike', query),
            ('default_code', 'ilike', query),
            ('sale_ok', '=', True),
            ('active', '=', True),
        ], limit=15, order='name')
        return {
            'products': [{
                'id': p.id,
                'name': p.display_name,
                'ref': p.default_code or '',
                'price': p.lst_price,
                'uom': p.uom_id.name,
            } for p in products]
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Descarga de recibo (PDF)
    # ──────────────────────────────────────────────────────────────────────────

    @http.route(
        '/my/field-service/<int:order_id>/receipt',
        type='http', auth='user', website=True
    )
    def portal_fso_receipt(self, order_id, access_token=None, **kw):
        order_sudo = self._fso_check_access(order_id, access_token)
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'hojas_de_trabajo.action_report_fso_receipt', [order_sudo.id]
        )
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'inline; filename="Recibo-%s.pdf"' % order_sudo.name),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _fso_check_access(self, order_id, access_token=None):
        """Verifica acceso y retorna el record con sudo si autorizado."""
        try:
            order_sudo = self._document_check_access(
                'field.service.order', order_id, access_token=access_token
            )
        except (AccessError, MissingError):
            raise AccessError(_('No tienes acceso a esta orden de servicio.'))
        return order_sudo

    def _check_is_technician(self, order_sudo):
        """Verifica que el usuario actual es el técnico asignado."""
        if order_sudo.technician_id and order_sudo.technician_id.id != request.env.user.id:
            # Responsables internos también pueden operar
            if not request.env.user.has_group(
                'hojas_de_trabajo.group_field_service_user'
            ):
                raise AccessError(
                    _('Solo el técnico asignado puede realizar esta acción.')
                )
