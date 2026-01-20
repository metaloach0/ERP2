from odoo import models, fields, api


class BikeAccessory(models.Model):
    _name = 'bike.accessory'
    _description = 'Accessoire de Velo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char(string='Nom', required=True, tracking=True)
    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                           default=lambda self: 'Nouveau')
    
    category = fields.Selection([
        ('helmet', 'Casque'),
        ('lock', 'Antivol'),
        ('light', 'Eclairage'),
        ('pump', 'Pompe'),
        ('bag', 'Sacoche'),
        ('bottle', 'Bidon/Porte-bidon'),
        ('rack', 'Porte-bagages'),
        ('basket', 'Panier'),
        ('bell', 'Sonnette'),
        ('mirror', 'Retroviseur'),
        ('mudguard', 'Garde-boue'),
        ('chain', 'Chaine'),
        ('tire', 'Pneu'),
        ('tube', 'Chambre a air'),
        ('brake', 'Frein'),
        ('pedal', 'Pedale'),
        ('saddle', 'Selle'),
        ('handlebar', 'Guidon'),
        ('clothing', 'Vetement'),
        ('tool', 'Outil'),
        ('other', 'Autre'),
    ], string='Categorie', required=True, default='other', tracking=True)

    brand = fields.Char(string='Marque')
    description = fields.Html(string='Description')
    image_1920 = fields.Image(string='Image')
    image_128 = fields.Image(string='Image miniature', related='image_1920', max_width=128, max_height=128, store=True)

    sale_price = fields.Monetary(string='Prix de vente', currency_field='currency_id', required=True)
    cost_price = fields.Monetary(string='Prix d\'achat', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Devise',
                                  default=lambda self: self.env.company.currency_id)

    stock_quantity = fields.Integer(string='Quantite en stock', default=0)
    stock_min = fields.Integer(string='Stock minimum', default=5)
    
    is_low_stock = fields.Boolean(string='Stock bas', compute='_compute_is_low_stock', store=True)

    product_id = fields.Many2one('product.product', string='Produit associe', ondelete='set null')

    compatible_bike_types = fields.Selection([
        ('all', 'Tous types'),
        ('road', 'Velo de route'),
        ('mountain', 'VTT'),
        ('city', 'Velo de ville'),
        ('electric', 'Velo electrique'),
    ], string='Compatible avec', default='all')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.company)

    _sql_constraints = [
        ('reference_uniq', 'unique (reference)', 'La reference de l\'accessoire doit etre unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('bike.accessory') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('stock_quantity', 'stock_min')
    def _compute_is_low_stock(self):
        for accessory in self:
            accessory.is_low_stock = accessory.stock_quantity <= accessory.stock_min

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
                'sale_ok': True,
                'purchase_ok': True,
            }
            product = self.env['product.product'].create(product_vals)
            self.product_id = product
        return self.product_id

    def action_restock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reapprovisionner',
            'res_model': 'bike.accessory.restock.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_accessory_ids': [(6, 0, self.ids)]},
        }
