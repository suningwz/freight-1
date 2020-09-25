from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

daftar_hari = ('Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu')

class DORekapPrintWizard(models.TransientModel):
    _name = 'do.rekap.shift.print.wizard'
    _description = 'Wizard untuk cetak rekap do per shift'

    date_start = fields.Date(string='Tanggal mulai', required=True, default=fields.Date.today)
    date_end = fields.Date(string='Tanggal akhir', required=True, default=fields.Date.today)
    pos = fields.Many2one(comodel_name='pos.gardu', required=True, string='pos')
    shift = fields.Many2one(comodel_name='pos.shift', required=True, string='Shift')
    
    
    
    @api.multi
    def action_get_report(self):
        hari = daftar_hari[self.date_start.weekday()]
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'hari'  : hari,
                'pos_id'    : self.pos.id,
                'shift_id'  : self.shift.id,
                'pos'   : self.pos.name,
                'shift' : self.shift.name,
                'date_start': self.date_start,
                'date_end': self.date_end,
            }
        }
        return self.env.ref('freight.recap_shift_report').report_action(self, data=data)


class DORekapPrint(models.AbstractModel):
    _name = 'report.freight.do_rekap_shift_print_wizard_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        hari = data['form']['hari']
        pos_id = data['form']['pos_id']
        shift_id = data['form']['shift_id']
        pos = data['form']['pos']
        shift = data['form']['shift']
        date_start = data['form']['date_start']
        date_end = datetime.strftime(datetime.strptime(data['form']['date_start'],'%Y-%m-%d'),'%d-%B-%Y')
        date_start_obj = datetime.strptime(date_start+' 00:00:00', '%Y-%m-%d %H:%M:%S')
        date_end_obj = datetime.strptime(date_start+' 23:59:59', '%Y-%m-%d %H:%M:%S')
        date_diff = (date_end_obj - date_start_obj).days + 1

        docs = []
        self.env.cr.execute(
            """
            select a.gardu, a.shift, d.name as kendaraan, c.name as produk, count(a.do_id) as qty
                from 
	                freight_attendance a
                left join 
                    (product_product b left join product_template c on b.product_tmpl_id=c.id ) on a.produk = b.id
                left join
                    tipe_kendaraan d on a.tipe_kendaraan = d.id
                left join
                    delivery_order e on a.do_id = e.id
                where a.tanggal = '%s' and gardu = %s and shift = %s and (e.state='open' or e.state='done') 
                group by a.gardu, a.shift, d.name, c.name
                order by a.gardu, a.shift, d.name, c.name
            """ % (date_start, pos_id, shift_id))

        hasil = self.env.cr.fetchall()
        for baris in hasil:
            docs.append({
                'pos' : baris[0],
                'shift' : baris[1],
                'kendaraan': baris[2],
                'produk': baris[3],
                'qty': baris[4]
            })
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'pos': pos,
            'shift': shift,
            'hari': hari,
            'docs': docs
        }
    
