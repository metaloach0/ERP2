from odoo import http
from odoo.http import request


class BikeShopWebsite(http.Controller):

    @http.route('/', type='http', auth='public', website=True, sitemap=False)
    def homepage(self, **kwargs):
        return request.redirect('/shop/bikes')

    @http.route(['/shop', '/bikes'], type='http', auth='public', website=True, sitemap=False)
    def shop_redirect(self, **kwargs):
        return request.redirect('/shop/bikes')

    @http.route('/shop/bikes', type='http', auth='public', website=True)
    def bikes_catalog(self, bike_type=None, category_id=None, **kwargs):
        domain = [
            ('is_for_sale', '=', True),
            ('state', '=', 'available'),
            ('stock_quantity', '>', 0),
        ]
        
        if bike_type:
            domain.append(('bike_type', '=', bike_type))
        if category_id:
            domain.append(('category_id', '=', int(category_id)))
        
        bikes = request.env['bike.bike'].sudo().search(domain)
        categories = request.env['bike.category'].sudo().search([])
        bike_types = dict(request.env['bike.bike']._fields['bike_type'].selection)
        
        return request.render('bike_shop.bikes_catalog', {
            'bikes': bikes,
            'categories': categories,
            'bike_types': bike_types,
            'current_type': bike_type,
            'current_category': int(category_id) if category_id else None,
        })

    @http.route('/shop/bike/<int:bike_id>', type='http', auth='public', website=True)
    def bike_detail(self, bike_id, **kwargs):
        bike = request.env['bike.bike'].sudo().browse(bike_id)
        if not bike.exists():
            return request.redirect('/shop/bikes')
        
        related_bikes = request.env['bike.bike'].sudo().search([
            ('category_id', '=', bike.category_id.id),
            ('id', '!=', bike.id),
            ('is_for_sale', '=', True),
            ('state', '=', 'available'),
            ('stock_quantity', '>', 0),
        ], limit=4)
        
        return request.render('bike_shop.bike_detail', {
            'bike': bike,
            'related_bikes': related_bikes,
        })

    @http.route('/shop/accessories', type='http', auth='public', website=True)
    def accessories_catalog(self, category=None, **kwargs):
        domain = [('stock_quantity', '>', 0)]
        
        if category:
            domain.append(('category', '=', category))
        
        accessories = request.env['bike.accessory'].sudo().search(domain)
        categories = dict(request.env['bike.accessory']._fields['category'].selection)
        
        return request.render('bike_shop.accessories_catalog', {
            'accessories': accessories,
            'categories': categories,
            'current_category': category,
        })

    @http.route('/shop/accessory/<int:accessory_id>', type='http', auth='public', website=True)
    def accessory_detail(self, accessory_id, **kwargs):
        accessory = request.env['bike.accessory'].sudo().browse(accessory_id)
        if not accessory.exists():
            return request.redirect('/shop/accessories')
        
        related = request.env['bike.accessory'].sudo().search([
            ('category', '=', accessory.category),
            ('id', '!=', accessory.id),
            ('stock_quantity', '>', 0),
        ], limit=4)
        
        return request.render('bike_shop.accessory_detail', {
            'accessory': accessory,
            'related_accessories': related,
        })

    @http.route('/rental/info', type='http', auth='public', website=True)
    def rental_info(self, **kwargs):
        
        pricing = request.env['bike.rental.pricing'].sudo().search([])
        bike_types = dict(request.env['bike.bike']._fields['bike_type'].selection)
        
        return request.render('bike_shop.rental_info', {
            'pricing': pricing,
            'bike_types': bike_types,
        })

    @http.route('/about', type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        return request.render('bike_shop.about_page')

    @http.route('/contact', type='http', auth='public', website=True)
    def contact_page(self, **kwargs):
        return request.render('bike_shop.contact_page')
