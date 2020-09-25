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
        if self.do_id.attendance_state == 'checked_in':
            wizard_form = self.env.ref('wk_wizard_messages.wizard_message_form', False)
            view_id = self.env['wk.wizard.message']
            partial_id = view_id.create({'text':'''
                Proses Checked-in DO 
                nomor : %s
                kendaraan : %s
                produk : %s
                sukses 
                ''' % (self.do_id.name, self.do_id.tipe_kendaraan.name, self.do_id.produk.name)}).id
            return {
                'name':'Informasi',
                'type': 'ir.actions.act_window',
                'res_model': 'wk.wizard.message',
                'res_id': partial_id,
                'view_id': wizard_form.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
            }
        elif self.do_id.attendance_state == 'checked_out' :
            wizard_form = self.env.ref('wk_wizard_messages.wizard_message_form', False)
            view_id = self.env['wk.wizard.message']
            partial_id = view_id.create({'text':'''
                Proses Checked-out DO
                nomor : %s
                kendaraan : %s
                produk : %s
                sukses 
                ''' % (self.do_id.name, self.do_id.tipe_kendaraan.name, self.do_id.produk.name)}).id
            return {
                'name':'Informasi',
                'type': 'ir.actions.act_window',
                'res_model': 'wk.wizard.message',
                'res_id': partial_id,
                'view_id': wizard_form.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
            }
        else:
            raise UserError('''
                DO telah dipergunakan !!!
                ''' 
            )
        # return
        kiosk_url = self.env['ir.config_parameter'].get_param('kiosk.url')
        return {
            'type'      : 'ir.actions.act_url',
            'url'       : kiosk_url,
            'target'    : 'self',
        }

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



    
