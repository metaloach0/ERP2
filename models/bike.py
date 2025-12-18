# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import datetime


class Bike(models.Model):
    _name = 'bike.bike'
    _description = 'Vélo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nom du vélo',
        required=True,
        tracking=True
    )
    
    reference = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    
    category_id = fields.Many2one(
        'bike.category',
        string='Catégorie',
        required=True,
        tracking=True
    )
    
    brand = fields.Char(
        string='Marque',
        required=True
    )
    
    model = fields.Char(
        string='Modèle',
        required=True
    )
    
    frame_size = fields.Selection([
        ('xs', 'XS (< 160cm)'),
        ('s', 'S (160-170cm)'),
        ('m', 'M (170-180cm)'),
        ('l', 'L (180-190cm)'),
        ('xl', 'XL (> 190cm)'),
    ], string='Taille du cadre')
    
    wheel_size = fields.Selection([
        ('20', '20"'),
        ('24', '24"'),
        ('26', '26"'),
        ('27.5', '27.5"'),
        ('28', '28"'),
        ('29', '29"'),
    ], string='Taille des roues')
    
    color = fields.Char(string='Couleur')
    
    weight = fields.Float(
        string='Poids (kg)',
        help='Poids du vélo en kilogrammes'
    )
    
    year = fields.Integer(
        string='Année',
        default=lambda self: datetime.now().year
    )
    
    description = fields.Text(string='Description')
    
    purchase_price = fields.Float(
        string="Prix d'achat",
        tracking=True
    )
    
    sale_price = fields.Float(
        string='Prix de vente',
        tracking=True
    )
    
    available_for_rent = fields.Boolean(
        string='Disponible à la location',
        default=True,
        tracking=True
    )
    
    rental_price_hour = fields.Float(
        string='Prix location/heure',
        help='Tarif de location à l\'heure'
    )
    
    rental_price_day = fields.Float(
        string='Prix location/jour',
        help='Tarif de location à la journée'
    )
    
    rental_price_week = fields.Float(
        string='Prix location/semaine',
        help='Tarif de location à la semaine'
    )
    
    rental_price_month = fields.Float(
        string='Prix location/mois',
        help='Tarif de location au mois'
    )
    
    state = fields.Selection([
        ('available', 'Disponible'),
        ('rented', 'Loué'),
        ('maintenance', 'En maintenance'),
        ('sold', 'Vendu'),
        ('retired', 'Retiré'),
    ], string='État', default='available', required=True, tracking=True)
    
    rental_contract_ids = fields.One2many(
        'rental.contract',
        'bike_id',
        string='Contrats de location'
    )
    
    active_rental_id = fields.Many2one(
        'rental.contract',
        string='Location en cours',
        compute='_compute_active_rental',
        store=True
    )
    
    rental_count = fields.Integer(
        string='Nombre de locations',
        compute='_compute_rental_count',
        store=True
    )
    
    image_1920 = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920
    )
    
    image_128 = fields.Image(
        string='Image (128)',
        related='image_1920',
        max_width=128,
        max_height=128,
        store=True
    )
    
    @api.depends('rental_contract_ids', 'rental_contract_ids.state')
    def _compute_active_rental(self):
        for bike in self:
            active_rental = bike.rental_contract_ids.filtered(
                lambda r: r.state == 'ongoing'
            )
            bike.active_rental_id = active_rental[:1] if active_rental else False
    
    @api.depends('rental_contract_ids')
    def _compute_rental_count(self):
        for bike in self:
            bike.rental_count = len(bike.rental_contract_ids)
    
    @api.constrains('sale_price', 'purchase_price')
    def _check_prices(self):
        for bike in self:
            if bike.sale_price < 0 or bike.purchase_price < 0:
                raise exceptions.ValidationError(
                    "Les prix doivent être positifs !"
                )
    
    @api.constrains('rental_price_hour', 'rental_price_day', 'rental_price_week', 'rental_price_month')
    def _check_rental_prices(self):
        for bike in self:
            if any(price < 0 for price in [
                bike.rental_price_hour,
                bike.rental_price_day,
                bike.rental_price_week,
                bike.rental_price_month
            ]):
                raise exceptions.ValidationError(
                    "Les prix de location doivent être positifs !"
                )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('bike.bike') or 'New'
        return super(Bike, self).create(vals_list)
    
    def action_set_available(self):
        self.write({'state': 'available'})
    
    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})
    
    def action_view_rentals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Locations',
            'res_model': 'rental.contract',
            'view_mode': 'list,form',
            'domain': [('bike_id', '=', self.id)],
            'context': {'default_bike_id': self.id}
        }
    
    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'La référence du vélo doit être unique !')
    ]