# Bike Shop - Module Odoo 19 pour Magasin de Velos

Module Odoo complet pour la gestion d'un magasin de velos avec vente, location et site web e-commerce.

## Fonctionnalites

### Gestion des Velos
- Catalogue complet avec categories (route, VTT, ville, electrique, enfant)
- Fiches produit detaillees (taille, couleur, materiau, vitesses, poids)
- Gestion du stock et des prix de vente
- Statuts de disponibilite (disponible, loue, maintenance, vendu)

### Gestion des Accessoires
- Catalogue d'accessoires par categorie (casques, antivols, eclairage, etc.)
- Gestion du stock avec alertes de reapprovisionnement
- Prix et marges

### Systeme de Location
- Tarification flexible (heure, jour, semaine, mois)
- Grille tarifaire par type de velo
- Contrats de location avec conditions
- Gestion des cautions
- Suivi des retards et penalites
- Historique complet des locations

### Wizards
- **Assistant de creation de locations** : Creer plusieurs locations en une seule operation
- **Assistant de prolongation** : Prolonger facilement une location en cours

### Gestion des Clients
- Fiches clients avec preferences (type de velo, taille)
- Historique des locations et achats
- Programme de fidelite (points)
- Statistiques client

### Reporting
- Analyse des locations (revenus, durees, taux d'occupation)
- Analyse du catalogue (stock, prix, marges)
- Vues pivot et graphiques

### Site Web
- Catalogue en ligne des velos a vendre
- Catalogue des accessoires
- Page de location avec reservation en ligne
- Pages A propos et Contact

## Installation

### Prerequis
- Odoo 19.0 Community
- PostgreSQL 15+
- Docker et Docker Compose (recommande)

### Avec Docker (recommande)

1. Cloner le repository :
```bash
git clone https://github.com/votre-repo/bike_shop.git
cd bike_shop
```

2. Lancer les conteneurs :
```bash
docker-compose up -d
```

3. Acceder a Odoo : http://localhost:8069

4. Creer une base de donnees et installer le module `bike_shop`

### Installation manuelle

1. Copier le dossier `bike_shop` dans le repertoire `addons` d'Odoo

2. Redemarrer Odoo :
```bash
./odoo-bin -c odoo.conf -u bike_shop
```

3. Activer le mode developpeur dans Odoo

4. Aller dans Apps > Mettre a jour la liste des applications

5. Rechercher "Bike Shop" et installer

## Modules dependants

Le module depend des modules Odoo suivants :
- `base`
- `sale_management`
- `stock`
- `account`
- `website_sale`
- `contacts`

## Structure du module

```
bike_shop/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── data/
│   ├── bike_category_data.xml
│   ├── bike_sequence_data.xml
│   ├── demo_data.xml
│   └── rental_pricing_data.xml
├── models/
│   ├── __init__.py
│   ├── accessory.py
│   ├── bike.py
│   ├── bike_category.py
│   ├── customer.py
│   ├── rental.py
│   ├── rental_contract.py
│   └── rental_pricing.py
├── report/
│   ├── rental_report_views.xml
│   └── sales_report_views.xml
├── security/
│   ├── bike_shop_security.xml
│   └── ir.model.access.csv
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       └── css/
│           ├── bike_shop.css
│           └── website_bike_shop.css
├── views/
│   ├── accessory_views.xml
│   ├── bike_views.xml
│   ├── customer_views.xml
│   ├── menu_views.xml
│   ├── rental_contract_views.xml
│   ├── rental_views.xml
│   └── website_templates.xml
└── wizard/
    ├── __init__.py
    ├── extend_rental_wizard.py
    ├── extend_rental_wizard_views.xml
    ├── rental_wizard.py
    └── rental_wizard_views.xml
```

## Configuration

### Grille tarifaire
Aller dans Bike Shop > Configuration > Grille tarifaire pour ajuster les prix de location.

### Categories
Aller dans Bike Shop > Configuration > Categories pour gerer les categories de velos.

### Groupes utilisateurs
- **Utilisateur Bike Shop** : Acces en lecture/ecriture aux velos, locations, clients
- **Responsable Bike Shop** : Acces complet incluant la configuration

## Donnees de demonstration

Le module inclut des donnees de demo :
- 4 clients
- 8 velos de differents types
- 10 accessoires
- Grille tarifaire complete

Pour charger les donnees de demo, cocher "Charger les donnees de demonstration" lors de la creation de la base.

## Utilisation

### Creer une location
1. Aller dans Bike Shop > Locations > Nouvelle location
2. Ou utiliser le wizard : Bike Shop > Locations > Nouvelle location (wizard)

### Prolonger une location
1. Ouvrir une location en cours
2. Cliquer sur "Prolonger" dans le menu Action
3. Remplir le formulaire du wizard

### Consulter les rapports
Aller dans Bike Shop > Reporting pour acceder aux analyses.

## Site Web

Les pages du site sont accessibles aux URLs suivantes :
- `/shop/bikes` - Catalogue des velos
- `/shop/accessories` - Catalogue des accessoires
- `/rental` - Page de location
- `/about` - A propos
- `/contact` - Contact

## Licence

LGPL-3

## Auteur

Bike Shop Team

## Support

Pour toute question, ouvrir une issue sur le repository GitHub.
