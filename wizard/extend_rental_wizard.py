from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class BikeRentalExtendWizard(models.TransientModel):
    _name = 'bike.rental.extend.wizard'
    _description = 'Assistant de prolongation de location'

    rental_id = fields.Many2one('bike.rental', string='Location', required=True)
    bike_id = fields.Many2one('bike.bike', string='Velo', related='rental_id.bike_id', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Client', related='rental_id.customer_id', readonly=True)
    
    current_date_end = fields.Datetime(string='Date de fin actuelle', related='rental_id.date_end', readonly=True)
    current_total = fields.Monetary(string='Montant actuel', related='rental_id.total_price', readonly=True,
                                    currency_field='currency_id')

    extension_type = fields.Selection([
        ('hours', 'Heures'),
        ('days', 'Jours'),
        ('weeks', 'Semaines'),
        ('months', 'Mois'),
    ], string='Type de prolongation', required=True, default='days')
    
    extension_duration = fields.Integer(string='Duree de prolongation', required=True, default=1)
    
    new_date_end = fields.Datetime(string='Nouvelle date de fin', compute='_compute_new_date_end', store=True)
    
    extension_price = fields.Monetary(string='Cout de la prolongation', compute='_compute_extension_price',
                                      currency_field='currency_id')
    new_total = fields.Monetary(string='Nouveau total', compute='_compute_extension_price',
                                currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    reason = fields.Text(string='Raison de la prolongation')
    apply_discount = fields.Boolean(string='Appliquer une remise', default=False)
    discount_percent = fields.Float(string='Remise (%)', default=0)

    @api.depends('current_date_end', 'extension_type', 'extension_duration')
    def _compute_new_date_end(self):
        for wizard in self:
            if wizard.current_date_end and wizard.extension_duration:
                if wizard.extension_type == 'hours':
                    delta = timedelta(hours=wizard.extension_duration)
                elif wizard.extension_type == 'days':
                    delta = timedelta(days=wizard.extension_duration)
                elif wizard.extension_type == 'weeks':
                    delta = timedelta(weeks=wizard.extension_duration)
                elif wizard.extension_type == 'months':
                    delta = timedelta(days=wizard.extension_duration * 30)
                else:
                    delta = timedelta(0)
                wizard.new_date_end = wizard.current_date_end + delta
            else:
                wizard.new_date_end = wizard.current_date_end

    @api.depends('extension_type', 'extension_duration', 'rental_id', 'apply_discount', 'discount_percent')
    def _compute_extension_price(self):
        for wizard in self:
            if wizard.rental_id and wizard.extension_duration:
                bike = wizard.rental_id.bike_id
                
                if wizard.extension_type == 'hours':
                    unit_price = bike.rental_price_hour or 0
                elif wizard.extension_type == 'days':
                    unit_price = bike.rental_price_day or 0
                elif wizard.extension_type == 'weeks':
                    unit_price = bike.rental_price_week or 0
                elif wizard.extension_type == 'months':
                    unit_price = bike.rental_price_month or 0
                else:
                    unit_price = 0

                extension_cost = unit_price * wizard.extension_duration
                
                if wizard.apply_discount and wizard.discount_percent > 0:
                    discount = extension_cost * wizard.discount_percent / 100
                    extension_cost -= discount

                wizard.extension_price = extension_cost
                wizard.new_total = wizard.current_total + extension_cost
            else:
                wizard.extension_price = 0
                wizard.new_total = wizard.current_total

    @api.constrains('extension_duration')
    def _check_extension_duration(self):
        for wizard in self:
            if wizard.extension_duration <= 0:
                raise ValidationError("La duree de prolongation doit etre superieure a 0.")

    def action_extend(self):
        self.ensure_one()
        
        if self.rental_id.state not in ['confirmed', 'ongoing', 'overdue']:
            raise UserError("Seule une location en cours ou confirmee peut etre prolongee.")

        overlapping = self.env['bike.rental'].search([
            ('id', '!=', self.rental_id.id),
            ('bike_id', '=', self.bike_id.id),
            ('state', 'not in', ['cancelled', 'returned']),
            ('date_start', '<', self.new_date_end),
            ('date_end', '>', self.rental_id.date_end),
        ])
        if overlapping:
            raise ValidationError(
                f"Le velo {self.bike_id.name} est deja reserve pour la periode de prolongation."
            )

        old_date_end = self.rental_id.date_end
        old_total = self.rental_id.total_price
        
        self.rental_id.write({
            'date_end': self.new_date_end,
        })

        if self.rental_id.state == 'overdue':
            self.rental_id.write({'state': 'ongoing'})

        self.rental_id.message_post(
            body=f"""
            <p><strong>Location prolongee</strong></p>
            <ul>
                <li>Ancienne date de fin: {old_date_end}</li>
                <li>Nouvelle date de fin: {self.new_date_end}</li>
                <li>Prolongation: {self.extension_duration} {dict(self._fields['extension_type'].selection).get(self.extension_type)}</li>
                <li>Cout supplementaire: {self.extension_price} {self.currency_id.symbol}</li>
                {f'<li>Raison: {self.reason}</li>' if self.reason else ''}
            </ul>
            """,
            subject="Location prolongee"
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Location prolongee',
            'res_model': 'bike.rental',
            'res_id': self.rental_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
