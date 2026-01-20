from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_bike_customer = fields.Boolean(string='Client Bike Shop', default=False)
    
    rental_ids = fields.One2many('bike.rental', 'customer_id', string='Locations')
    rental_count = fields.Integer(string='Nombre de locations', compute='_compute_rental_stats')
    rental_total_spent = fields.Monetary(string='Total depense en locations', compute='_compute_rental_stats',
                                         currency_field='currency_id')
    
    contract_ids = fields.One2many('bike.rental.contract', 'customer_id', string='Contrats')
    contract_count = fields.Integer(string='Nombre de contrats', compute='_compute_contract_count')

    preferred_bike_type = fields.Selection([
        ('road', 'Velo de route'),
        ('mountain', 'VTT'),
        ('city', 'Velo de ville'),
        ('electric', 'Velo electrique'),
        ('hybrid', 'Velo hybride'),
    ], string='Type de velo prefere')

    bike_size = fields.Selection([
        ('xs', 'XS (< 155 cm)'),
        ('s', 'S (155-165 cm)'),
        ('m', 'M (165-175 cm)'),
        ('l', 'L (175-185 cm)'),
        ('xl', 'XL (185-195 cm)'),
        ('xxl', 'XXL (> 195 cm)'),
    ], string='Taille de velo')

    customer_since = fields.Date(string='Client depuis')
    loyalty_points = fields.Integer(string='Points de fidelite', default=0)
    
    id_document_on_file = fields.Boolean(string='Piece d\'identite enregistree', default=False)
    
    customer_notes = fields.Text(string='Notes client')

    has_active_rental = fields.Boolean(string='Location active', compute='_compute_has_active_rental')
    current_rental_id = fields.Many2one('bike.rental', string='Location en cours', compute='_compute_has_active_rental')

    @api.depends('rental_ids', 'rental_ids.state', 'rental_ids.total_price')
    def _compute_rental_stats(self):
        for partner in self:
            rentals = partner.rental_ids.filtered(lambda r: r.state != 'cancelled')
            partner.rental_count = len(rentals)
            partner.rental_total_spent = sum(rentals.mapped('total_price'))

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for partner in self:
            partner.contract_count = len(partner.contract_ids)

    @api.depends('rental_ids', 'rental_ids.state')
    def _compute_has_active_rental(self):
        for partner in self:
            active = partner.rental_ids.filtered(lambda r: r.state in ['confirmed', 'ongoing'])
            partner.has_active_rental = bool(active)
            partner.current_rental_id = active[0] if active else False

    def action_view_rentals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Locations',
            'res_model': 'bike.rental',
            'view_mode': 'list,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrats',
            'res_model': 'bike.rental.contract',
            'view_mode': 'list,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
        }

    def action_create_rental(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouvelle location',
            'res_model': 'bike.rental',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_customer_id': self.id},
        }

    def action_add_loyalty_points(self, points):
        for partner in self:
            partner.loyalty_points += points

    @api.model
    def get_or_create_bike_customer(self, vals):
        partner = self.search([('email', '=', vals.get('email'))], limit=1)
        if not partner:
            vals['is_bike_customer'] = True
            vals['customer_since'] = fields.Date.today()
            partner = self.create(vals)
        else:
            if not partner.is_bike_customer:
                partner.write({
                    'is_bike_customer': True,
                    'customer_since': partner.customer_since or fields.Date.today(),
                })
        return partner
