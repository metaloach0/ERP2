# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BikeCategory(models.Model):
    _name = 'bike.category'
    _description = 'Catégorie de vélo'
    _order = 'name'

    name = fields.Char(
        string='Nom de la catégorie',
        required=True,
        translate=True
    )
    
    code = fields.Char(
        string='Code',
        required=True,
        help='Code unique pour la catégorie'
    )
    
    description = fields.Text(
        string='Description'
    )
    
    bike_ids = fields.One2many(
        'bike.bike',
        'category_id',
        string='Vélos'
    )
    
    bike_count = fields.Integer(
        string='Nombre de vélos',
        compute='_compute_bike_count',
        store=True
    )
    
    active = fields.Boolean(
        default=True
    )
    
    @api.depends('bike_ids')
    def _compute_bike_count(self):
        for category in self:
            category.bike_count = len(category.bike_ids)
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Le code de la catégorie doit être unique !')
    ]