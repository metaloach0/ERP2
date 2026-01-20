from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class BikeRentalWizard(models.TransientModel):
    _name = 'bike.rental.wizard'
    _description = 'Assistant de creation de locations'

    customer_id = fields.Many2one('res.partner', string='Client', required=True)
    create_contract = fields.Boolean(string='Creer un contrat', default=True)
    contract_type = fields.Selection([
        ('short', 'Courte duree (< 1 semaine)'),
        ('medium', 'Moyenne duree (1-4 semaines)'),
        ('long', 'Longue duree (> 1 mois)'),
    ], string='Type de contrat', default='short')

    date_start = fields.Datetime(string='Date de debut', required=True,
                                 default=fields.Datetime.now)
    date_end = fields.Datetime(string='Date de fin', required=True)
    duration_type = fields.Selection([
        ('hour', 'Heure'),
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ], string='Type de duree', required=True, default='day')

    bike_ids = fields.Many2many('bike.bike', string='Velos a louer',
                                domain=[('is_for_rent', '=', True), ('state', '=', 'available')])
    
    line_ids = fields.One2many('bike.rental.wizard.line', 'wizard_id', string='Lignes de location')

    include_accessories = fields.Boolean(string='Inclure des accessoires', default=False)
    accessory_ids = fields.Many2many('bike.accessory', string='Accessoires')

    total_amount = fields.Monetary(string='Montant total', compute='_compute_totals',
                                   currency_field='currency_id')
    total_deposit = fields.Monetary(string='Caution totale', compute='_compute_totals',
                                    currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    discount_percent = fields.Float(string='Remise (%)', default=0)
    notes = fields.Text(string='Notes')

    @api.depends('line_ids.subtotal', 'line_ids.deposit', 'discount_percent')
    def _compute_totals(self):
        for wizard in self:
            subtotal = sum(wizard.line_ids.mapped('subtotal'))
            discount = subtotal * wizard.discount_percent / 100
            wizard.total_amount = subtotal - discount
            wizard.total_deposit = sum(wizard.line_ids.mapped('deposit'))

    @api.onchange('bike_ids', 'date_start', 'date_end', 'duration_type')
    def _onchange_bikes(self):
        if self.bike_ids:
            lines = []
            for bike in self.bike_ids:
                price_field = f'rental_price_{self.duration_type}'
                unit_price = getattr(bike, price_field, 0) or 0
                
                if self.date_start and self.date_end:
                    delta = self.date_end - self.date_start
                    total_hours = delta.total_seconds() / 3600
                    
                    if self.duration_type == 'hour':
                        duration = int(total_hours)
                    elif self.duration_type == 'day':
                        duration = max(1, int(total_hours / 24))
                    elif self.duration_type == 'week':
                        duration = max(1, int(total_hours / 168))
                    elif self.duration_type == 'month':
                        duration = max(1, int(total_hours / 720))
                    else:
                        duration = 1
                else:
                    duration = 1

                lines.append((0, 0, {
                    'bike_id': bike.id,
                    'unit_price': unit_price,
                    'duration': duration,
                    'deposit': unit_price * 2,
                }))
            self.line_ids = [(5, 0, 0)] + lines

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_start and wizard.date_end:
                if wizard.date_end <= wizard.date_start:
                    raise ValidationError("La date de fin doit etre posterieure a la date de debut.")

    def action_create_rentals(self):
        self.ensure_one()
        
        if not self.line_ids:
            raise UserError("Veuillez ajouter au moins un velo a louer.")

        for line in self.line_ids:
            overlapping = self.env['bike.rental'].search([
                ('bike_id', '=', line.bike_id.id),
                ('state', 'not in', ['cancelled', 'returned']),
                ('date_start', '<', self.date_end),
                ('date_end', '>', self.date_start),
            ])
            if overlapping:
                raise ValidationError(
                    f"Le velo {line.bike_id.name} n'est pas disponible pour cette periode."
                )

        contract = False
        if self.create_contract:
            contract = self.env['bike.rental.contract'].create({
                'customer_id': self.customer_id.id,
                'contract_type': self.contract_type,
                'date_start': self.date_start.date(),
                'date_end': self.date_end.date(),
                'discount_percent': self.discount_percent,
                'notes': self.notes,
                'terms_accepted': True,
            })

        rentals = self.env['bike.rental']
        for line in self.line_ids:
            rental_vals = {
                'bike_id': line.bike_id.id,
                'customer_id': self.customer_id.id,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'duration_type': self.duration_type,
                'unit_price': line.unit_price,
                'deposit': line.deposit,
                'notes': self.notes,
            }
            if contract:
                rental_vals['contract_id'] = contract.id
            if self.include_accessories and self.accessory_ids:
                rental_vals['accessories_ids'] = [(6, 0, self.accessory_ids.ids)]
            
            rental = self.env['bike.rental'].create(rental_vals)
            rentals |= rental

        if contract:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contrat cree',
                'res_model': 'bike.rental.contract',
                'res_id': contract.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            if len(rentals) == 1:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Location creee',
                    'res_model': 'bike.rental',
                    'res_id': rentals.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Locations creees',
                    'res_model': 'bike.rental',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rentals.ids)],
                    'target': 'current',
                }


class BikeRentalWizardLine(models.TransientModel):
    _name = 'bike.rental.wizard.line'
    _description = 'Ligne du wizard de location'

    wizard_id = fields.Many2one('bike.rental.wizard', string='Wizard', required=True, ondelete='cascade')
    bike_id = fields.Many2one('bike.bike', string='Velo', required=True,
                              domain=[('is_for_rent', '=', True), ('state', '=', 'available')])
    
    unit_price = fields.Monetary(string='Prix unitaire', currency_field='currency_id')
    duration = fields.Integer(string='Duree', default=1)
    subtotal = fields.Monetary(string='Sous-total', compute='_compute_subtotal',
                               currency_field='currency_id')
    deposit = fields.Monetary(string='Caution', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='wizard_id.currency_id')

    @api.depends('unit_price', 'duration')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.unit_price * line.duration

    @api.onchange('bike_id')
    def _onchange_bike(self):
        if self.bike_id and self.wizard_id:
            duration_type = self.wizard_id.duration_type
            price_field = f'rental_price_{duration_type}'
            self.unit_price = getattr(self.bike_id, price_field, 0) or 0
            self.deposit = self.unit_price * 2
