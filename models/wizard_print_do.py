from odoo import api, fields, models


class WizardPrintDo(models.TransientModel):
    _name = 'wizard.print.do'
    _description = 'wizard cetak barcode DO'

    do_start = fields.Many2one(comodel_name='delivery.order', required="1", string='Nomor DO awal')
    do_end = fields.Many2one(comodel_name='delivery.order', required="1", string='Nomor DO akhir')
    digit = fields.Integer(string="Jumlah digit", default=11)

    def action_print_do(self):
        self.env.cr.execute("DELETE FROM print_do")
        seq = 1
        records = self.env['delivery.order'].search([('name','>=',self.do_start.name),('name','<=',self.do_end.name),('state','=','open')])
        for rec in records:
            if len(rec.name) == self.digit :
                if seq == 1:
                    curr_id = self.env['print.do'].create({'do1_id': rec.id})
                    seq += 1
                elif seq == 2:
                    curr_id.write({'do2_id': rec.id})
                    seq += 1
                elif seq == 3:
                    curr_id.write({'do3_id': rec.id})
                    seq += 1
                else:
                    curr_id.write({'do4_id': rec.id})
                    seq = 1
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'do_start': self.do_start,
                'do_end': self.do_end,   
            }
        }
        return self.env.ref('freight.action_report_barcode_member_batch').report_action(self,data=data)


class PrintDOBatch(models.AbstractModel):
    _name = 'report.freight.report_barcode_do_new4'


    @api.model
    def _get_report_values(self, docids, data=None):
        do_start = data['form']['do_start']
        do_end = data['form']['do_end']
        docs = []
        data_do = self.env['print.do'].search([])
        for rec in data_do:
            docs.append({
                'name1': rec.do1_id.name,
                'kendaraan1': rec.do1_id.tipe_kendaraan.name,
                'produk1': rec.do1_id.produk.name,
                'barcode1': rec.do1_id.barcode_image,
                'name2': rec.do2_id.name,
                'kendaraan2': rec.do2_id.tipe_kendaraan.name,
                'produk2': rec.do2_id.produk.name,
                'barcode2': rec.do2_id.barcode_image,
                'name3': rec.do3_id.name,
                'kendaraan3': rec.do3_id.tipe_kendaraan.name,
                'produk3': rec.do3_id.produk.name,
                'barcode3': rec.do3_id.barcode_image,
                'name4': rec.do4_id.name,
                'kendaraan4': rec.do4_id.tipe_kendaraan.name,
                'produk4': rec.do4_id.produk.name,
                'barcode4': rec.do4_id.barcode_image,
            })
        return {
            'doc_ids' : data['ids'],
            'doc_model': data['model'],
            'do_start': do_start,
            'do_end': do_end,
            'docs': docs,
        }
    
