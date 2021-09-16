from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class WizardDOCancel(models.TransientModel):
    _name = 'freight.wizard_do_cancel'
    _description = 'Wizard untuk checkin/checkout manual atau cancel order'

    do_id = fields.Many2one(comodel_name='delivery.order', string='Nomor DO')
    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan')
    produk = fields.Many2one(comodel_name='product.product', string='Produk')
    date = fields.Date(string='Tgl DO', default=fields.Date.today())
    expired_date = fields.Date(string='Tgl. Kadaluwarsa')
    keterangan = fields.Text(string='Keterangan')

    def action_check_do(self):
        new_id = self.env['delivery.order'].attendance_scan(self.do_id.name)
        temp = new_id["action"];
        return temp;

    def action_cancel_do(self):
        if self.keterangan :
            new_id = self.env['delivery.order'].browse(self.do_id.id)
            new_id.write({
                'state': 'cancel',
                'keterangan': self.keterangan,
            })
        else:
            raise UserError('Untuk membatalkan harap diisi keterangan.') 
        return

    @api.onchange('do_id')
    def update_detail(self):
        self.tipe_kendaraan = self.do_id.tipe_kendaraan.id
        self.produk = self.do_id.produk.id
        self.date = self.do_id.date
        self.expired_date = self.do_id.expired_date



    
