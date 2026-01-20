{
    'name': 'Bike Shop - Vente et Location de Velos',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Gestion complete d\'un magasin de velos: vente, location, accessoires',
    'description': """
Bike Shop - Module de Gestion de Magasin de Velos
=================================================

Ce module permet de gerer:
- Catalogue de velos (modeles, tailles, types)
- Pieces detachees et accessoires
- Vente de velos et accessoires
- Location de velos (heure, jour, semaine, mois)
- Contrats de location avec tarification dynamique
- Gestion de la disponibilite des velos
- Fiches clients avec historique
- Reporting: ventes, taux d'occupation, revenus

Fonctionnalites avancees:
- Wizard pour creation de locations en masse
- Wizard pour prolongation de locations
- Site web e-commerce integre
- Dashboard de reporting
    """,
    'author': 'Bike Shop Team',
    'website': 'https://github.com/votre-repo/bike_shop',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'stock',
        'account',
        'website_sale',
        'contacts',
    ],
    'data': [
        # Security
        'security/bike_shop_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/bike_category_data.xml',
        'data/bike_sequence_data.xml',
        'data/rental_pricing_data.xml',
        # Views
        'views/bike_views.xml',
        'views/accessory_views.xml',
        'views/rental_views.xml',
        'views/rental_contract_views.xml',
        'views/customer_views.xml',
        # Wizards (must be before menus)
        'wizard/rental_wizard_views.xml',
        'wizard/extend_rental_wizard_views.xml',
        # Reports (must be before menus)
        'report/rental_report_views.xml',
        'report/sales_report_views.xml',
        # Menus (after all actions are defined)
        'views/menu_views.xml',
        # Website
        'views/website_templates.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bike_shop/static/src/css/bike_shop.css',
        ],
        'web.assets_frontend': [
            'bike_shop/static/src/css/website_bike_shop.css',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
