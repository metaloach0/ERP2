from odoo import models, fields, api


class RentalPricing(models.Model):
    _name = 'bike.rental.pricing'
    _description = 'Grille tarifaire de location'
    _order = 'bike_type, duration_type'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    bike_type = fields.Selection([
        ('road', 'Velo de route'),
        ('mountain', 'VTT'),
        ('city', 'Velo de ville'),
        ('electric', 'Velo electrique'),
        ('hybrid', 'Velo hybride'),
        ('bmx', 'BMX'),
        ('folding', 'Velo pliant'),
        ('cargo', 'Velo cargo'),
        ('kids', 'Velo enfant'),
    ], string='Type de velo', required=True)

    duration_type = fields.Selection([
        ('hour', 'Heure'),
        ('day', 'Jour'),
        ('week', 'Semaine'),
        ('month', 'Mois'),
    ], string='Unite de duree', required=True, default='day')

    price = fields.Monetary(string='Prix', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    min_duration = fields.Integer(string='Duree minimum', default=1)
    deposit_amount = fields.Monetary(string='Caution', currency_field='currency_id')
    
    is_weekend_price = fields.Boolean(string='Tarif week-end', default=False)
    weekend_surcharge = fields.Float(string='Majoration week-end (%)', default=0)

    season = fields.Selection([
        ('all', 'Toute l\'annee'),
        ('high', 'Haute saison'),
        ('low', 'Basse saison'),
    ], string='Saison', default='all')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_pricing', 'unique (bike_type, duration_type, season, company_id)',
         'Une grille tarifaire existe deja pour ce type de velo et cette duree!')
    ]

    @api.depends('bike_type', 'duration_type', 'season')
    def _compute_name(self):
        bike_type_labels = dict(self._fields['bike_type'].selection)
        duration_labels = dict(self._fields['duration_type'].selection)
        season_labels = dict(self._fields['season'].selection)
        for record in self:
            bike_label = bike_type_labels.get(record.bike_type, '')
            duration_label = duration_labels.get(record.duration_type, '')
            season_label = season_labels.get(record.season, '')
            record.name = f"{bike_label} - {duration_label} ({season_label})"

    @api.model
    def get_price(self, bike_type, duration_type, season='all'):
        pricing = self.search([
            ('bike_type', '=', bike_type),
            ('duration_type', '=', duration_type),
            ('season', '=', season),
        ], limit=1)
        if not pricing and season != 'all':
            pricing = self.search([
                ('bike_type', '=', bike_type),
                ('duration_type', '=', duration_type),
                ('season', '=', 'all'),
            ], limit=1)
        return pricing.price if pricing else 0.0
