# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class RentalPricing(models.Model):
    _name = 'rental.pricing'
    _description = 'Tarification de location'
    _order = 'category_id, duration_type'

    name = fields.Char(
        string='Nom',
        compute='_compute_name',
        store=True
    )
    
    category_id = fields.Many2one(
        'bike.category',
        string='Catégorie de vélo',
        required=True
    )
    
    duration_type = fields.Selection([
        ('hour', 'Heure'),
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ], string='Type de durée', required=True)
    
    price = fields.Float(
        string='Prix',
        required=True
    )
    
    active = fields.Boolean(
        default=True
    )
    
    @api.depends('category_id', 'duration_type')
    def _compute_name(self):
        for record in self:
            if record.category_id and record.duration_type:
                duration_labels = {
                    'hour': 'Heure',
                    'day': 'Jour',
                    'week': 'Semaine',
                    'month': 'Mois',
                }
                record.name = f"{record.category_id.name} - {duration_labels.get(record.duration_type, '')}"
            else:
                record.name = 'Nouveau tarif'
    
    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price < 0:
                raise exceptions.ValidationError("Le prix doit être positif !")
    
    _sql_constraints = [
        ('category_duration_unique', 
         'unique(category_id, duration_type)', 
         'Une tarification existe déjà pour cette catégorie et cette durée !')
    ]