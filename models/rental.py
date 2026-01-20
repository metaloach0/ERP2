from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class BikeRental(models.Model):
    _name = 'bike.rental'
    _description = 'Location de Velo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                      default=lambda self: 'Nouveau')
    
    bike_id = fields.Many2one('bike.bike', string='Velo', required=True, tracking=True,
                              domain=[('is_for_rent', '=', True), ('state', '=', 'available')])
    customer_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    contract_id = fields.Many2one('bike.rental.contract', string='Contrat', ondelete='set null')

    date_start = fields.Datetime(string='Date de debut', required=True, tracking=True,
                                 default=fields.Datetime.now)
    date_end = fields.Datetime(string='Date de fin prevue', required=True, tracking=True)
    date_returned = fields.Datetime(string='Date de retour effectif', tracking=True)

    duration_type = fields.Selection([
        ('hour', 'Heure'),
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ], string='Type de duree', required=True, default='day')

    duration = fields.Integer(string='Duree', compute='_compute_duration', store=True)
    duration_display = fields.Char(string='Duree affichee', compute='_compute_duration')

    unit_price = fields.Monetary(string='Prix unitaire', currency_field='currency_id')
    total_price = fields.Monetary(string='Prix total', compute='_compute_total_price', store=True,
                                  currency_field='currency_id')
    deposit = fields.Monetary(string='Caution', currency_field='currency_id')
    deposit_returned = fields.Boolean(string='Caution rendue', default=False)
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmee'),
        ('ongoing', 'En cours'),
        ('returned', 'Retournee'),
        ('cancelled', 'Annulee'),
        ('overdue', 'En retard'),
    ], string='Statut', default='draft', required=True, tracking=True)

    notes = fields.Text(string='Notes')
    bike_condition_start = fields.Text(string='Etat du velo au depart')
    bike_condition_end = fields.Text(string='Etat du velo au retour')

    is_overdue = fields.Boolean(string='En retard', compute='_compute_is_overdue', store=True)
    overdue_days = fields.Integer(string='Jours de retard', compute='_compute_is_overdue', store=True)
    late_fee = fields.Monetary(string='Frais de retard', compute='_compute_late_fee', store=True,
                               currency_field='currency_id')

    accessories_ids = fields.Many2many('bike.accessory', string='Accessoires inclus')

    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.company)
    
    invoice_id = fields.Many2one('account.move', string='Facture', readonly=True, copy=False)
    invoice_state = fields.Selection(related='invoice_id.state', string='Statut facture', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.rental') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('date_start', 'date_end', 'duration_type')
    def _compute_duration(self):
        for rental in self:
            if rental.date_start and rental.date_end:
                delta = rental.date_end - rental.date_start
                total_hours = delta.total_seconds() / 3600
                
                if rental.duration_type == 'hour':
                    rental.duration = int(total_hours)
                    rental.duration_display = f"{int(total_hours)} heure(s)"
                elif rental.duration_type == 'day':
                    days = max(1, int(total_hours / 24))
                    rental.duration = days
                    rental.duration_display = f"{days} jour(s)"
                elif rental.duration_type == 'week':
                    weeks = max(1, int(total_hours / 168))
                    rental.duration = weeks
                    rental.duration_display = f"{weeks} semaine(s)"
                elif rental.duration_type == 'month':
                    months = max(1, int(total_hours / 720))
                    rental.duration = months
                    rental.duration_display = f"{months} mois"
                else:
                    rental.duration = 0
                    rental.duration_display = ''
            else:
                rental.duration = 0
                rental.duration_display = ''

    @api.depends('duration', 'unit_price')
    def _compute_total_price(self):
        for rental in self:
            rental.total_price = rental.duration * rental.unit_price

    @api.depends('date_end', 'date_returned', 'state')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for rental in self:
            if rental.state in ['ongoing', 'confirmed'] and rental.date_end:
                if now > rental.date_end:
                    rental.is_overdue = True
                    delta = now - rental.date_end
                    rental.overdue_days = delta.days
                else:
                    rental.is_overdue = False
                    rental.overdue_days = 0
            elif rental.state == 'returned' and rental.date_returned and rental.date_end:
                if rental.date_returned > rental.date_end:
                    rental.is_overdue = True
                    delta = rental.date_returned - rental.date_end
                    rental.overdue_days = delta.days
                else:
                    rental.is_overdue = False
                    rental.overdue_days = 0
            else:
                rental.is_overdue = False
                rental.overdue_days = 0

    @api.depends('is_overdue', 'overdue_days', 'unit_price')
    def _compute_late_fee(self):
        for rental in self:
            if rental.is_overdue and rental.overdue_days > 0:
                daily_rate = rental.unit_price if rental.duration_type == 'day' else rental.unit_price / 24
                rental.late_fee = daily_rate * rental.overdue_days * 1.5
            else:
                rental.late_fee = 0

    @api.onchange('bike_id', 'duration_type')
    def _onchange_bike_pricing(self):
        if self.bike_id and self.duration_type:
            price_field = f'rental_price_{self.duration_type}'
            if hasattr(self.bike_id, price_field):
                self.unit_price = getattr(self.bike_id, price_field) or 0

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rental in self:
            if rental.date_start and rental.date_end:
                if rental.date_end <= rental.date_start:
                    raise ValidationError("La date de fin doit etre posterieure a la date de debut.")

    @api.constrains('bike_id', 'date_start', 'date_end', 'state')
    def _check_bike_availability(self):
        for rental in self:
            if rental.state not in ['cancelled', 'returned']:
                overlapping = self.search([
                    ('id', '!=', rental.id),
                    ('bike_id', '=', rental.bike_id.id),
                    ('state', 'not in', ['cancelled', 'returned']),
                    ('date_start', '<', rental.date_end),
                    ('date_end', '>', rental.date_start),
                ])
                if overlapping:
                    raise ValidationError(
                        f"Le velo {rental.bike_id.name} est deja reserve pour cette periode."
                    )

    def action_confirm(self):
        for rental in self:
            if rental.state != 'draft':
                raise UserError("Seule une location en brouillon peut etre confirmee.")
            rental.write({'state': 'confirmed'})
            rental.bike_id.write({'state': 'reserved'})

    def action_start(self):
        for rental in self:
            if rental.state != 'confirmed':
                raise UserError("Seule une location confirmee peut demarrer.")
            rental.write({
                'state': 'ongoing',
                'date_start': fields.Datetime.now(),
            })
            rental.bike_id.write({'state': 'rented'})

    def action_return(self):
        for rental in self:
            if rental.state != 'ongoing':
                raise UserError("Seule une location en cours peut etre retournee.")
            rental.write({
                'state': 'returned',
                'date_returned': fields.Datetime.now(),
            })
            rental.bike_id.write({'state': 'available'})

    def action_cancel(self):
        for rental in self:
            if rental.state in ['returned']:
                raise UserError("Impossible d'annuler une location deja retournee.")
            old_state = rental.state
            rental.write({'state': 'cancelled'})
            if old_state in ['confirmed', 'ongoing']:
                rental.bike_id.write({'state': 'available'})

    def action_return_deposit(self):
        for rental in self:
            if rental.state != 'returned':
                raise UserError("La caution ne peut etre rendue qu'apres le retour du velo.")
            rental.write({'deposit_returned': True})

    def action_extend_rental(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prolonger la location',
            'res_model': 'bike.rental.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_rental_id': self.id},
        }

    @api.model
    def _cron_check_overdue(self):
        now = fields.Datetime.now()
        overdue_rentals = self.search([
            ('state', '=', 'ongoing'),
            ('date_end', '<', now),
        ])
        for rental in overdue_rentals:
            rental.write({'state': 'overdue'})
            rental.message_post(
                body=f"La location est en retard depuis {rental.overdue_days} jour(s).",
                subject="Location en retard"
            )

    def action_create_invoice(self):
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError("Une facture existe deja pour cette location.")
        
        if self.state == 'draft':
            raise UserError("Impossible de facturer une location en brouillon.")
        
        income_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
        ], limit=1)
        
        if not income_account:
            income_account = self.env['account.account'].search([
                ('account_type', 'in', ['income', 'income_other']),
            ], limit=1)
        
        if not income_account:
            income_account = self.env['account.account'].search([
                ('code', '=like', '7%'),
            ], limit=1)
        
        if not income_account:
            raise UserError("Aucun compte de revenus trouve. Veuillez configurer la comptabilite.")
        
        invoice_lines = []
        
        duration_labels = {
            'hour': 'heure(s)',
            'day': 'jour(s)',
            'week': 'semaine(s)',
            'month': 'mois',
        }
        duration_label = duration_labels.get(self.duration_type, '')
        
        invoice_lines.append((0, 0, {
            'name': f"Location velo: {self.bike_id.name} - {self.duration} {duration_label}",
            'quantity': self.duration,
            'price_unit': self.unit_price,
            'account_id': income_account.id,
        }))
        
        if self.late_fee > 0:
            invoice_lines.append((0, 0, {
                'name': f"Frais de retard ({self.overdue_days} jour(s))",
                'quantity': 1,
                'price_unit': self.late_fee,
                'account_id': income_account.id,
            }))
        
        for accessory in self.accessories_ids:
            invoice_lines.append((0, 0, {
                'name': f"Accessoire: {accessory.name}",
                'quantity': 1,
                'price_unit': 0,
                'account_id': income_account.id,
            }))
        
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'narration': f"Location du {self.date_start.strftime('%d/%m/%Y')} au {self.date_end.strftime('%d/%m/%Y')}",
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'invoice_id': invoice.id})
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facture',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError("Aucune facture pour cette location.")
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facture',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
