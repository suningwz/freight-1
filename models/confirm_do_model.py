#*- coding: utf-8 -*-
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class ConfirmDo(models.Model):
    _name = 'confirm.do'
    _description = 'Konfirmasi DO'
    
    do_start = fields.Char(string='DO Awal')
    do_end = fields.Char(string='DO Akhir')
    customer_do = fields.Many2one(comodel_name='customer.do', string='Customer')
    total_do = fields.Integer(string='Total DO', default=0)
    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan',index=True)
    number_do  = fields.Char(string='Nomor DO')
    produk = fields.Many2one(comodel_name='product.product', string='Produk',index=True)
    confirmed = fields.Boolean(string='Confirmed', default=False)
    CreatedDo_date = fields.Date(string='Created Date',index=True)
    confirmedDo_date = fields.Date(string='Confirmed Date', index=True)
    confirmedDo_by = fields.Many2one(comodel_name='res.users', string='Confirmed By',)

    @api.multi
    def button_confirm_do(self):
        records = self.env['delivery.order'].search([('name','>=',self.do_start),('name','<=',self.do_end),('state','=','draft')])
        for rec in records:
            if rec.state == 'draft':
                rec.state = 'open'
                rec.sudo().action_generate_barcode()
                self.confirmed =True
                self.confirmedDo_date = fields.Datetime.now().strftime('%Y-%m-%d')
                self.confirmedDo_by = self.env.user.id

        return {
            'name'      : 'Confirm DO',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'kanban,form',
            'res_model' : 'confirm.do',
            'target'    : 'current',
        }

    def button_cetak_do(self):
        do_start=self.env['delivery.order'].search([('name','=',self.do_start),('state','=','open')])
        do_end=self.env['delivery.order'].search([('name','=',self.do_end),('state','=','open')])
        return {    
            'name': "Cetak DO secara batch",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.print.do',
            'target': 'new',
            'context': {'default_do_start': do_start.id, 'default_do_end': do_end.id}
        }
    