from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BikeRentalContract(models.Model):
    _name = 'bike.rental.contract'
    _description = 'Contrat de Location de Velo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_contract desc'

    name = fields.Char(string='Numero de contrat', required=True, copy=False, readonly=True,
                      default=lambda self: 'Nouveau')
    
    customer_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    
    date_contract = fields.Date(string='Date du contrat', required=True,
                               default=fields.Date.today, tracking=True)
    date_start = fields.Date(string='Date de debut', required=True, tracking=True)
    date_end = fields.Date(string='Date de fin', required=True, tracking=True)

    contract_type = fields.Selection([
        ('short', 'Courte duree (< 1 semaine)'),
        ('medium', 'Moyenne duree (1-4 semaines)'),
        ('long', 'Longue duree (> 1 mois)'),
        ('subscription', 'Abonnement'),
    ], string='Type de contrat', required=True, default='short', tracking=True)

    rental_ids = fields.One2many('bike.rental', 'contract_id', string='Locations')
    rental_count = fields.Integer(string='Nombre de locations', compute='_compute_rental_count')

    total_amount = fields.Monetary(string='Montant total', compute='_compute_totals', store=True,
                                   currency_field='currency_id')
    total_deposit = fields.Monetary(string='Caution totale', compute='_compute_totals', store=True,
                                    currency_field='currency_id')
    amount_paid = fields.Monetary(string='Montant paye', currency_field='currency_id', tracking=True)
    balance_due = fields.Monetary(string='Solde du', compute='_compute_balance', store=True,
                                  currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirme'),
        ('active', 'Actif'),
        ('done', 'Termine'),
        ('cancelled', 'Annule'),
    ], string='Statut', default='draft', required=True, tracking=True)

    discount_percent = fields.Float(string='Remise (%)', default=0)
    discount_amount = fields.Monetary(string='Montant remise', compute='_compute_discount',
                                      currency_field='currency_id')

    terms_accepted = fields.Boolean(string='Conditions acceptees', tracking=True)
    id_document_type = fields.Selection([
        ('id_card', 'Carte d\'identite'),
        ('passport', 'Passeport'),
        ('driver_license', 'Permis de conduire'),
    ], string='Type de piece d\'identite')
    id_document_number = fields.Char(string='Numero de piece')
    
    notes = fields.Text(string='Notes')
    special_conditions = fields.Text(string='Conditions particulieres')

    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.rental.contract') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('rental_ids')
    def _compute_rental_count(self):
        for contract in self:
            contract.rental_count = len(contract.rental_ids)

    @api.depends('rental_ids.total_price', 'rental_ids.deposit', 'discount_percent')
    def _compute_totals(self):
        for contract in self:
            subtotal = sum(contract.rental_ids.mapped('total_price'))
            discount = subtotal * contract.discount_percent / 100
            contract.total_amount = subtotal - discount
            contract.total_deposit = sum(contract.rental_ids.mapped('deposit'))

    @api.depends('discount_percent', 'rental_ids.total_price')
    def _compute_discount(self):
        for contract in self:
            subtotal = sum(contract.rental_ids.mapped('total_price'))
            contract.discount_amount = subtotal * contract.discount_percent / 100

    @api.depends('total_amount', 'amount_paid')
    def _compute_balance(self):
        for contract in self:
            contract.balance_due = contract.total_amount - contract.amount_paid

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for contract in self:
            if contract.date_start and contract.date_end:
                if contract.date_end < contract.date_start:
                    raise ValidationError("La date de fin doit etre posterieure ou egale a la date de debut.")

    @api.constrains('terms_accepted')
    def _check_terms(self):
        for contract in self:
            if contract.state == 'confirmed' and not contract.terms_accepted:
                raise ValidationError("Les conditions generales doivent etre acceptees pour confirmer le contrat.")

    @api.onchange('contract_type', 'date_start')
    def _onchange_contract_type(self):
        if self.contract_type and self.date_start:
            from datetime import timedelta
            if self.contract_type == 'short':
                self.date_end = self.date_start + timedelta(days=7)
            elif self.contract_type == 'medium':
                self.date_end = self.date_start + timedelta(days=28)
            elif self.contract_type == 'long':
                self.date_end = self.date_start + timedelta(days=90)
            elif self.contract_type == 'subscription':
                self.date_end = self.date_start + timedelta(days=365)

    def action_confirm(self):
        for contract in self:
            if not contract.terms_accepted:
                raise ValidationError("Veuillez accepter les conditions generales.")
            if not contract.rental_ids:
                raise ValidationError("Le contrat doit contenir au moins une location.")
            contract.write({'state': 'confirmed'})
            for rental in contract.rental_ids:
                if rental.state == 'draft':
                    rental.action_confirm()

    def action_activate(self):
        for contract in self:
            contract.write({'state': 'active'})
            for rental in contract.rental_ids:
                if rental.state == 'confirmed':
                    rental.action_start()

    def action_done(self):
        for contract in self:
            contract.write({'state': 'done'})

    def action_cancel(self):
        for contract in self:
            contract.write({'state': 'cancelled'})
            for rental in contract.rental_ids:
                if rental.state not in ['returned', 'cancelled']:
                    rental.action_cancel()

    def action_view_rentals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Locations',
            'res_model': 'bike.rental',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id, 'default_customer_id': self.customer_id.id},
        }

    def action_print_contract(self):
        return self.env.ref('bike_shop.action_report_rental_contract').report_action(self)
