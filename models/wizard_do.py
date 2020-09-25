from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class WizardDO(models.TransientModel):
    _name = 'freight.wizard_do'
    _description = 'Model for create delivery order'

    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan')
    produk = fields.Many2one(comodel_name='product.product', string='Produk')
    total_do = fields.Integer(string='Total DO', default=0)
    qty = fields.Float(string='Qty', default=0)
    date = fields.Date(string='Tgl DO', default=fields.Date.today())
    expired_date = fields.Date(string='Tgl. Kadaluwarsa')
    

    def action_create_do(self):
        for n in range(self.total_do):
            name = self.env['ir.sequence'].next_by_code('do_sequence')
            vals = {
                'name' : name,
                'tipe_kendaraan' : self.tipe_kendaraan.id,
                'produk': self.produk.id,
                'qty': self.qty,
                'date' : self.date,
                'expired_date': self.expired_date,
            }
            new_id = self.env['delivery.order'].create(vals)
            new_id.action_generate_barcode()
        return {
            'name'      : 'Delivery order',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'tree,form,pivot',
            'res_model' : 'delivery.order',
            'target'    : 'current',
        }

    def action_cancel(self):
        return

    @api.onchange("date")
    def _onchange_date(self):
        tenggat = self.env.user.company_id.tenggat
        self.expired_date= fields.Datetime.to_string(fields.Datetime.from_string(self.date)+relativedelta(months=tenggat))
