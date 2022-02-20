from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class WizardDO(models.TransientModel):
    _name = 'freight.wizard_do'
    _description = 'Model for create delivery order'

    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan')
    produk = fields.Many2one(comodel_name='product.product', string='Produk')
    total_do = fields.Integer(string='Total DO', default=0)
    customer_do = fields.Many2one(comodel_name='customer.do', string='Customer')
    qty = fields.Float(string='Qty', default=0)
    date = fields.Date(string='Tgl DO', default=fields.Date.today())
    expired_date = fields.Date(string='Tgl. Kadaluwarsa')

    def action_create_do(self):
        count = 1
        do_start =0
        do_end=0 
        for n in range(self.total_do):
            name = self.env['ir.sequence'].next_by_code('do_sequence')
            vals = {
                'name' : name,
                'tipe_kendaraan' : self.tipe_kendaraan.id,
                'customer_do' : self.customer_do.id,
                'produk': self.produk.id,
                'qty': self.qty,
                'date' : self.date,
                'expired_date': self.expired_date,
            }
            new_id = self.env['delivery.order'].create(vals)
            new_id.action_generate_barcode()
            if count== 1:
                do_start = name
            do_end = name
            count+=1

        # self.env.cr.execute('''
        #     insert into confirm_do (do_start, do_end, do_cust, tipe_kendaraan, produk, total_do, confirmed, create_date, create_uid, write_date, write_uid)
        #     values (%s, %s, %s, %s, %s, %s, 0, now(), %s, now(), %s)
        #     ''' % (do_start.id, do_end.id, self.customer_do.id, self.tipe_kendaraan.id, self.produk.id, self.total_do, login_user.id, login_user.id) )
        
        confirm_vals = {
            'do_start' :do_start,
            'do_end' : do_end,
            'customer_do' : self.customer_do.id,
            'tipe_kendaraan' : self.tipe_kendaraan.id,
            'produk': self.produk.id,
            'total_do': self.total_do,
            'CreatedDo_date':self.date,
            'number_do':'%s - %s' %(do_start, do_end)
        }
        confirm_new_id = self.env['confirm.do'].create(confirm_vals)
        
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
