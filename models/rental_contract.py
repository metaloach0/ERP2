# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from datetime import timedelta


class RentalContract(models.Model):
    _name = 'rental.contract'
    _description = 'Contrat de location de vélo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    name = fields.Char(
        string='Numéro de contrat',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Client',
        required=True,
        tracking=True
    )
    
    bike_id = fields.Many2one(
        'bike.bike',
        string='Vélo',
        required=True,
        tracking=True,
        domain="[('available_for_rent', '=', True), ('state', '=', 'available')]"
    )
    
    start_date = fields.Datetime(
        string='Date de début',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    
    end_date = fields.Datetime(
        string='Date de fin',
        required=True,
        tracking=True
    )
    
    actual_return_date = fields.Datetime(
        string='Date de retour effective',
        tracking=True
    )
    
    duration_type = fields.Selection([
        ('hour', 'Heure'),
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ], string='Type de location', required=True, default='day')
    
    duration = fields.Float(
        string='Durée',
        compute='_compute_duration',
        store=True
    )
    
    unit_price = fields.Float(
        string='Prix unitaire',
        required=True
    )
    
    total_price = fields.Float(
        string='Prix total',
        compute='_compute_total_price',
        store=True
    )
    
    deposit = fields.Float(
        string='Caution',
        default=100.0
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('ongoing', 'En cours'),
        ('returned', 'Retourné'),
        ('cancelled', 'Annulé'),
    ], string='État', default='draft', required=True, tracking=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('start_date', 'end_date', 'duration_type')
    def _compute_duration(self):
        for contract in self:
            if contract.start_date and contract.end_date:
                delta = contract.end_date - contract.start_date
                
                if contract.duration_type == 'hour':
                    contract.duration = delta.total_seconds() / 3600
                elif contract.duration_type == 'day':
                    contract.duration = delta.days or 1
                elif contract.duration_type == 'week':
                    contract.duration = delta.days / 7
                elif contract.duration_type == 'month':
                    contract.duration = delta.days / 30
                else:
                    contract.duration = 0
            else:
                contract.duration = 0
    
    @api.depends('duration', 'unit_price')
    def _compute_total_price(self):
        for contract in self:
            contract.total_price = contract.duration * contract.unit_price
    
    @api.onchange('bike_id', 'duration_type')
    def _onchange_bike_duration(self):
        if self.bike_id and self.duration_type:
            price_field = f'rental_price_{self.duration_type}'
            self.unit_price = getattr(self.bike_id, price_field, 0.0)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for contract in self:
            if contract.end_date <= contract.start_date:
                raise exceptions.ValidationError(
                    "La date de fin doit être après la date de début !"
                )
    
    @api.constrains('bike_id', 'start_date', 'end_date')
    def _check_bike_availability(self):
        for contract in self:
            if contract.state in ['confirmed', 'ongoing']:
                overlapping = self.search([
                    ('id', '!=', contract.id),
                    ('bike_id', '=', contract.bike_id.id),
                    ('state', 'in', ['confirmed', 'ongoing']),
                    ('start_date', '<', contract.end_date),
                    ('end_date', '>', contract.start_date),
                ])
                if overlapping:
                    raise exceptions.ValidationError(
                        f"Le vélo {contract.bike_id.name} est déjà loué pour cette période !"
                    )
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract') or 'New'
        return super(RentalContract, self).create(vals_list)
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_start(self):
        self.write({'state': 'ongoing'})
        self.bike_id.write({'state': 'rented'})
    
    def action_return(self):
        self.write({
            'state': 'returned',
            'actual_return_date': fields.Datetime.now()
        })
        self.bike_id.write({'state': 'available'})
        return {
            'name': "Create Invoice",
            'type': "ir.actions.act_window",
            'res_model': "rental.create.invoice",
            'view_mode': 'form',
            'target': 'new'
        }
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        if self.bike_id.state == 'rented':
            self.bike_id.write({'state': 'available'})