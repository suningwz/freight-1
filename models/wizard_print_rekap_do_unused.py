from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

daftar_hari = ('Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu')

class DOUnusedRekapPrintWizard(models.TransientModel):
    _name = 'do.unused.rekap.print.wizard'
    _description = 'Wizard untuk cetak rekap do belum terpakai'

    date_start = fields.Date(string='Tanggal mulai', required=True, default=fields.Date.today)
    date_end = fields.Date(string='Tanggal akhir', required=True, default=fields.Date.today)
    
    @api.multi
    def action_get_report(self):
        hari = daftar_hari[self.date_start.weekday()]
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'hari'  : hari,
                'date_start': self.date_start,
                'date_end': self.date_end,
            }
        }
        return self.env.ref('freight.recap_report_unused').report_action(self, data=data)


class DOUnusedRekapPrint(models.AbstractModel):
    _name = 'report.freight.do_unused_rekap_print_wizard_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        hari = data['form']['hari']
        date_start = data['form']['date_start']
        date_end = datetime.strftime(datetime.strptime(data['form']['date_start'],'%Y-%m-%d'),'%d-%B-%Y')
        date_start_obj = datetime.strptime(date_start+' 00:00:00', '%Y-%m-%d %H:%M:%S')
        date_end_obj = datetime.strptime(date_start+' 23:59:59', '%Y-%m-%d %H:%M:%S')
        date_diff = (date_end_obj - date_start_obj).days + 1

        docs = []
        self.env.cr.execute(
            """
            select d.name as kendaraan, c.name as produk, count(a.id) as qty
                from
	                delivery_order a
                left join
                    (product_product b left join product_template c on b.product_tmpl_id=c.id ) on a.produk = b.id
                left join
                    tipe_kendaraan d on a.tipe_kendaraan = d.id
                where a.state='open' and a.active is true and a.attendance_state='checked_out'
                group by d.name, c.name
                order by d.name, c.name
            """)

        hasil = self.env.cr.fetchall()
        for baris in hasil:
            docs.append({
                'kendaraan': baris[0],
                'produk': baris[1],
                'qty': baris[2]
            })
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'hari': hari,
            'docs': docs
        }
    
