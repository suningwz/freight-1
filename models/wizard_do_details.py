from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import barcode
from barcode.writer import ImageWriter
import pyqrcode
import base64
import os

_logger = logging.getLogger(__name__)

class WizardDoDetails(models.TransientModel):
     _name = 'wizard.do.details'
     _description = 'Wizard untuk melihat list rekap nomer DO yg sudah masuk'

     nomor_do = fields.Char('Nomor DO')
     tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan')
     produk = fields.Many2one(comodel_name='product.product', string='Produk')
     check_in = fields.Datetime('Check In')
     tanggal = fields.Date('Tanggal')
     
# class DoDetails(models.Model):
#      _name = 'do.details'
#      _description = 'Model untuk melihat list rekap nomer DO yg sudah masuk'
     
#      name = fields.Char('')
#      tipe_kendaraan = fields.Char('')
#      produk = fields.Char('')
#      check_in = fields.Datetime('Check In')

#      @api.multi 
#      def _get_count_list(self):
#           data_obj    = self.env['example.object']
#           for data in self:       
#                     list_data        = data_obj.search([('Fill the condition')])
#                     data.example_count = len(list_data)
                    
#      def details_do(self):
#           self.env.cr.execute("DELETE FROM do_details where write_uid = %s  " %self.env.uid)
#           seq = 1
#           jam = datetime.now().time().hour + 7
#           login_user = self.env['res.users'].search([('id', '=', self.env.uid)])
#           if jam >= 0 and jam < 6 :
#                kemarin = datetime.now()-timedelta(days=1)
#                hari_ini = datetime.strftime(kemarin,'%Y-%m-%d')
#           else:
#                hari_ini = datetime.strftime(fields.Datetime.now(),'%Y-%m-%d')
#                if login_user.shift.name == 'Shift 1' and jam >= 29 and jam <=31:  
#                     hari_ini = datetime.strftime(fields.Date.today()+timedelta(days=1),'%Y-%m-%d')
#           records = self.env['freight.attendance'].search([('tanggal','=','2021-01-04'),('gardu','=',self.env.user.gardu.id),('shift','=',self.env.user.shift.id)])

#           for rec in records:
#                self.env.cr.execute('''
#                insert into do_details (name, tipe_kendaraan, produk, check_in,  create_date, create_uid, write_date, write_uid)
#                values ('%s', '%s', '%s', '%s', now(), %s, now(), %s)
#                ''' % (rec.do_id.name, rec.tipe_kendaraan.name, rec.produk.name, rec.check_in ,self.env.user.id, self.env.user.id) )
#                self.env.cr.commit()
               
#           return True
