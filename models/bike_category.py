from odoo import models, fields, api


class BikeCategory(models.Model):
    _name = 'bike.category'
    _description = 'Categorie de Velo'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    image = fields.Image(string='Image', max_width=256, max_height=256)
    parent_id = fields.Many2one('bike.category', string='Categorie parente', ondelete='cascade')
    child_ids = fields.One2many('bike.category', 'parent_id', string='Sous-categories')
    bike_count = fields.Integer(string='Nombre de velos', compute='_compute_bike_count')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Le code de categorie doit etre unique!')
    ]

    @api.depends('child_ids')
    def _compute_bike_count(self):
        for category in self:
            category.bike_count = self.env['bike.bike'].search_count([
                ('category_id', 'child_of', category.id)
            ])

    def name_get(self):
        result = []
        for record in self:
            if record.parent_id:
                name = f"{record.parent_id.name} / {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result
