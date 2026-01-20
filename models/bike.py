from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Bike(models.Model):
    _name = 'bike.bike'
    _description = 'Velo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom du modele', required=True, tracking=True)
    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                           default=lambda self: 'Nouveau')
    category_id = fields.Many2one('bike.category', string='Categorie', required=True, tracking=True)
    brand = fields.Char(string='Marque', required=True)
    model_year = fields.Char(string='Annee modele')
    
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
    ], string='Type', required=True, default='city', tracking=True)

    size = fields.Selection([
        ('xs', 'XS (< 155 cm)'),
        ('s', 'S (155-165 cm)'),
        ('m', 'M (165-175 cm)'),
        ('l', 'L (175-185 cm)'),
        ('xl', 'XL (185-195 cm)'),
        ('xxl', 'XXL (> 195 cm)'),
        ('kids', 'Enfant'),
    ], string='Taille', required=True, default='m')

    color = fields.Char(string='Couleur')
    frame_material = fields.Selection([
        ('aluminum', 'Aluminium'),
        ('carbon', 'Carbone'),
        ('steel', 'Acier'),
        ('titanium', 'Titane'),
    ], string='Materiau cadre', default='aluminum')

    wheel_size = fields.Selection([
        ('12', '12 pouces'),
        ('14', '14 pouces'),
        ('16', '16 pouces'),
        ('20', '20 pouces'),
        ('24', '24 pouces'),
        ('26', '26 pouces'),
        ('27.5', '27.5 pouces'),
        ('28', '28 pouces'),
        ('29', '29 pouces'),
    ], string='Taille des roues', default='28')

    gears_count = fields.Integer(string='Nombre de vitesses', default=21)
    weight = fields.Float(string='Poids (kg)')
    description = fields.Html(string='Description')
    
    image_1920 = fields.Image(string='Image')
    image_128 = fields.Image(string='Image miniature', related='image_1920', max_width=128, max_height=128, store=True)

    sale_price = fields.Monetary(string='Prix de vente', currency_field='currency_id', tracking=True)
    cost_price = fields.Monetary(string='Prix d\'achat', currency_field='currency_id')
    rental_price_hour = fields.Monetary(string='Prix location/heure', currency_field='currency_id')
    rental_price_day = fields.Monetary(string='Prix location/jour', currency_field='currency_id')
    rental_price_week = fields.Monetary(string='Prix location/semaine', currency_field='currency_id')
    rental_price_month = fields.Monetary(string='Prix location/mois', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    state = fields.Selection([
        ('available', 'Disponible'),
        ('rented', 'En location'),
        ('maintenance', 'En maintenance'),
        ('sold', 'Vendu'),
        ('reserved', 'Reserve'),
    ], string='Statut', default='available', tracking=True, required=True)

    is_for_sale = fields.Boolean(string='A vendre', default=True)
    is_for_rent = fields.Boolean(string='A louer', default=True)
    
    stock_quantity = fields.Integer(string='Quantite en stock', default=1)
    
    product_id = fields.Many2one('product.product', string='Produit associe', ondelete='set null')

    rental_ids = fields.One2many('bike.rental', 'bike_id', string='Historique locations')
    rental_count = fields.Integer(string='Nombre de locations', compute='_compute_rental_count')
    
    current_rental_id = fields.Many2one('bike.rental', string='Location en cours', compute='_compute_current_rental')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.company)

    _sql_constraints = [
        ('reference_uniq', 'unique (reference)', 'La reference du velo doit etre unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('bike.bike') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('rental_ids')
    def _compute_rental_count(self):
        for bike in self:
            bike.rental_count = len(bike.rental_ids)

    @api.depends('rental_ids', 'rental_ids.state')
    def _compute_current_rental(self):
        for bike in self:
            current = bike.rental_ids.filtered(lambda r: r.state == 'ongoing')
            bike.current_rental_id = current[0] if current else False

    @api.constrains('sale_price', 'rental_price_day')
    def _check_prices(self):
        for bike in self:
            if bike.is_for_sale and bike.sale_price <= 0:
                raise ValidationError("Le prix de vente doit etre superieur a 0 pour un velo a vendre.")
            if bike.is_for_rent and bike.rental_price_day <= 0:
                raise ValidationError("Le prix de location journalier doit etre superieur a 0 pour un velo a louer.")

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_view_rentals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Locations',
            'res_model': 'bike.rental',
            'view_mode': 'list,form',
            'domain': [('bike_id', '=', self.id)],
            'context': {'default_bike_id': self.id},
        }

    def _create_product(self):
        self.ensure_one()
        if not self.product_id:
            product_vals = {
                'name': self.name,
                'default_code': self.reference,
                'type': 'product',
                'list_price': self.sale_price,
                'standard_price': self.cost_price,
                'image_1920': self.image_1920,
                'sale_ok': self.is_for_sale,
                'purchase_ok': True,
            }
            product = self.env['product.product'].create(product_vals)
            self.product_id = product
        return self.product_id
