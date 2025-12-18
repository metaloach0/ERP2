from odoo import models, fields

class CreateInvoice(models.TransientModel):
    _name = "rental.create.invoice"
    _description = "rental.create.invoice"
    date = fields.Date() 

    def create_invoice(self):
        self.env['account.move'].create({'invoice_date': self.date,
        "move_type": "out_invoice"})


