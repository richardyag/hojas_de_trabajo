# -*- coding: utf-8 -*-
{
    'name': 'Field Service – Hojas de Trabajo',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Órdenes de servicio en campo con técnicos de portal',
    'description': """
        Módulo de gestión de servicios en campo (Field Service).

        Funcionalidades:
        - Creación y asignación de órdenes de servicio a técnicos (usuarios de portal)
        - Los técnicos gestionan su planilla desde el portal web (sin licencia interna)
        - Registro de materiales y servicios utilizados en cada visita
        - Integración con Órdenes de Venta
        - Cobro en campo: efectivo, tarjeta de crédito
        - Emisión de recibo en PDF
        - Captura de firma digital del cliente (canvas) con soporte para Odoo Sign
        - Trazabilidad completa y notificaciones por correo
    """,
    'author': 'Econovex',
    'website': 'https://www.econovex.com',
    'depends': [
        'base',
        'mail',
        'portal',
        'sale_management',
        'account',
        'product',
        'web',
    ],
    'data': [
        # Security (primero)
        'security/field_service_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/field_service_sequences.xml',
        'data/mail_templates.xml',
        # Views backend
        'views/field_service_order_views.xml',
        'views/field_service_menu.xml',
        # Portal
        'views/portal_templates.xml',
        # Reportes
        'report/field_service_report_action.xml',
        'report/field_service_report_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hojas_de_trabajo/static/src/css/portal.css',
            'hojas_de_trabajo/static/src/js/signature_pad.js',
            'hojas_de_trabajo/static/src/js/product_search.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
