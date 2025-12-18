# -*- coding: utf-8 -*-
{
    'name': 'Bike Rental & Sales',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestion de location et vente de vélos',
    'description': """
        Module de gestion pour magasin de vélos
        =========================================
        
        Fonctionnalités:
        * Catalogue de vélos et accessoires
        * Vente de vélos
        * Location de vélos (courte et longue durée)
        * Gestion des contrats de location
        * Tarification flexible (heure/jour/mois)
        * Suivi de disponibilité
        * Rapports de ventes et locations
    """,
    'author': 'Votre Groupe',
    'website': 'https://github.com/votregroupe/bike_rental',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'stock',
        'product',
        'contacts',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'data/sequence_data.xml',
        'data/bike_category_data.xml',
        'data/pricing_data.xml',
        'data/bike_data.xml',
        
        'views/bike_views.xml',
        'views/rental_contract_views.xml',
        'views/rental_pricing_views.xml',
        'views/menu_views.xml',
        'views/create_invoice.xml',
        
        'report/rental_report.xml',
        'report/rental_report_templates.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}