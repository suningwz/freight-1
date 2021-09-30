# -*- coding: utf-8 -*-

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

class DeliveryOrder(models.Model):
    _name = 'delivery.order'
    _description = 'Delivery Order untuk angkutan'

    name = fields.Char(string='Name', default='draft')
    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan', string='Tipe Kendaraan')
    produk = fields.Many2one(comodel_name='product.product', string='Produk')
    qty = fields.Float(string='Qty', default=0)
    date = fields.Date(string='Tgl DO', default=fields.Date.today())
    expired_date = fields.Date(string='Tgl. Kadauwarsa')
    gate_ids = fields.One2many(comodel_name='do.gate', inverse_name='do_id', string='gate ids')
    barcode_type = fields.Selection(string="Barcode type", selection=[('barcode','Barcode'),('qr', 'QR')], default='barcode')
    barcode_image = fields.Binary(string='Barcode Inage')
    state = fields.Selection(string='status', selection=[('draft', 'Draft'), ('open', 'Open'), ('done', 'Done'), ('cancel', 'Cancel')], default='draft')
    attendance_ids = fields.One2many('freight.attendance', 'do_id', help='list of attendances for the member')
    last_attendance_id = fields.Many2one('freight.attendance', compute='_compute_last_attendance_id')
    attendance_state = fields.Selection(string="Attendance", compute='_compute_attendance_state', selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")], store=True)
    keterangan = fields.Text(string='Keterangan')
    active = fields.Boolean(string='active',default=True)
    

    api.one
    def action_confirm(self):
        if self.state == 'draft':
            if self.name == 'draft':
                get_sequence = self.env['ir.sequence'].next_by_code('do_sequence')
                self.name = get_sequence
            self.state = 'open'
            self.sudo().action_generate_barcode()
        else :
            # usermessage = self.env['wk.wizard.message']
            # usermessage.genrated_message('Test')
            self.env.user.notify_info(message='DO dengan nomor %s tidak berstatus draft' % self.name)
            # wizard_form = self.env.ref('wk_wizard_messages.wizard_message_form', False)
            # view_id = self.env['wk.wizard.message']
            # partial_id = view_id.create({'text':'DO dengan nomor %s tidak berstatus draft' % self.name}).id
            # print('lewat sini broo!! : %s' % partial_id)
            # return {
            #     'name':'Hello World',
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'wk.wizard.message',
            #     'res_id': partial_id,
            #     'view_id': wizard_form.id,
            #     'view_mode': 'form',
            #     'view_type': 'form',
            #     'target': 'new',
            # }
    


    api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('date')
    def _onchange_date(self):
        tenggat = self.env.user.company_id.tenggat
        self.expired_date= fields.Datetime.to_string(fields.Datetime.from_string(self.date)+relativedelta(months=tenggat))
    
    @api.one
    def action_generate_barcode(self):
        if self.name:
            if self.barcode_type == 'qr':
                if os.name == 'nt':
                    filename = 'D:\\qr\\'+self.name+'.png'
                    qr_code = pyqrcode.create(self.name)
                    qr_code.png('D:\\qr\\'+self.name+'.png', scale=6)
                else:
                    filename = '/tmp/'+self.name+'.png'
                    qr_code = pyqrcode.create(self.name)
                    qr_code.png('/tmp/'+self.name+'.png', scale=6)
            else:
                code128 = barcode.get('code128', self.name, writer=ImageWriter())
                if os.name == 'nt':
                    filename = code128.save('D:\\qr\\bc'+self.name)
                else:
                    filename = code128.save('/tmp/'+self.name)
            f = open(filename, mode="rb")
            barcode_data = f.read()
            image_data = base64.encodestring(barcode_data)
            self.barcode_image = base64.b64encode(barcode_data)

    @api.model
    def attendance_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        member = self.search([('name', '=', barcode)], limit=1)
        return member and member.attendance_action('freight.freight_attendance_action_kiosk_mode') or \
            {'warning': _('No vehicle corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @api.multi
    def attendance_action(self, next_action):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        action_message = self.env.ref('freight.freight_attendance_action_greeting_message').read()[0]
        action_message['previous_attendance_change_date'] = self.last_attendance_id and (self.last_attendance_id.check_out or self.last_attendance_id.check_in) or False
        action_message['employee_name'] = self.name
        action_message['kendaraan'] = self.tipe_kendaraan.name
        action_message['produk']  =self.produk.name
        action_message['expired_date'] = self.expired_date
        action_message['keterangan'] = self.keterangan
        action_message['next_action'] = next_action
        
        if self.env.user:
            modified_attendance = self.sudo(self.env.user.id).attendance_action_change()
        else:
            modified_attendance = self.sudo().attendance_action_change()
        # modified_attendance = self.attendance_action_change()
        action_message['message'] = modified_attendance['message']
        action_message['attendance'] = modified_attendance['attendance'].read()[0]
        return {'action': action_message}

    @api.multi
    def attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()
        action_date_only = fields.Date.today()
        # print('start %s' % datetime.now())
        if self.attendance_state != 'checked_in' :
            if self.state == 'open':
                if self.expired_date >= action_date_only :
                    login_user = self.env['res.users'].search([('id', '=', self.env.uid)])
                    if login_user.shift.name == 'Shift 3' :
                        # print("lewat sini")
                        tanggal = (action_date + timedelta(hours=0)).strftime('%Y-%m-%d')
                    else :
                        tanggal = (action_date + timedelta(hours=7)).strftime('%Y-%m-%d')
                    # print('tanggal : %s' % tanggal)
                    self.env.cr.execute('''
                    insert into freight_attendance (do_id, gardu, shift, check_in, check_out, user_id, create_date, create_uid, write_date, write_uid, tipe_kendaraan, produk, state, tanggal)
                    values (%s, %s, %s, '%s', '%s', %s, now(), %s, now(), %s, %s, %s, 'done', '%s')
                    ''' % (self.id, login_user.gardu.id, login_user.shift.id, action_date,action_date, login_user.id, login_user.id, login_user.id, self.tipe_kendaraan.id, self.produk.id, tanggal) )
                    self.env.cr.commit()
                    # print('stop create attendaces %s' % datetime.now())
                    self.write({'state' : 'done',
                                'attendance_state' : 'checked_out',})
                    # self.env.cr.commit()
                    # print('stop commit %s' % datetime.now())
                    attendance = self.env['freight.attendance'].search([('do_id','=',self.id)], limit=1)
                    # print('stop checked-in  %s' % datetime.now())
                    return {
                        'attendance':attendance,
                        'message':'sukses'
                    }
                else:
                    attendance = self.env['freight.attendance'].search([('check_out', '=', False)], limit=1)
                    return {
                        'attendance':attendance,
                        'message':'DO Sudah Expired'
                    }
            elif self.state == 'cancel':
                attendance = self.env['freight.attendance'].search([('check_out', '=', False)], limit=1)
                return {
                    'attendance':attendance,
                    'message':'DO Di Blokir'
                }
            else:
                attendance = self.env['freight.attendance'].search([('do_id','=',self.id)], limit=1)
                return {
                    'attendance':attendance,
                    'message':'DO Sudah Terscan'
                }

        else:
            attendance = self.env['freight.attendance'].search([('check_out', '=', False)], limit=1)
            return {
                'attendance':attendance,
                'message':'lain-lain'
            }

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for member in self:
            member.last_attendance_id = member.attendance_ids and member.attendance_ids[0] or False

    @api.depends('last_attendance_id.check_in', 'last_attendance_id.check_out', 'last_attendance_id')
    def _compute_attendance_state(self):
        for member in self:
            member.attendance_state = member.last_attendance_id and not member.last_attendance_id.check_out and 'checked_in' or 'checked_out'

class DoGate(models.Model):
    _name = 'do.gate'
    _description = 'details gate untuk delivery order'

    name = fields.Char(string='Name')
    gate_id = fields.Many2one(comodel_name='gate', string='Gate')
    checkin = fields.Datetime(string='Jam Check in')
    do_id = fields.Many2one(comodel_name='delivery.order', string='do id')

class Gate(models.Model):
    _name = 'gate'
    _description = 'tabel gate'

    name = fields.Char(string='Name')

class TipeKendaraan(models.Model):
    _name = 'tipe.kendaraan'
    _description = 'tipe Kendaraan'

    name = fields.Char(string='Name')
    
class Attendance(models.Model):
    _name = "freight.attendance"
    _description = "Attendance"
    # _order = "check_in desc"

    do_id = fields.Many2one('delivery.order',
                                 string="DO id",
                                 required=True,
                                 store=True,
                                 index=False,
                                 )
    check_in = fields.Datetime(string="Check In",
                               default=fields.Datetime.now,
                               required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours',
                                compute='_compute_worked_hours',
                                store=True,
                                readonly=True)
    tipe_kendaraan = fields.Many2one(comodel_name='tipe.kendaraan',string='Tipe Kendaraan', related="do_id.tipe_kendaraan", store=True)
    produk = fields.Many2one(comodel_name='product.product', string='Produk', related="do_id.produk", store=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User')
    gardu = fields.Many2one(comodel_name='pos.gardu', string='Pos')
    shift = fields.Many2one(comodel_name='pos.shift',string='Shift')    
    state = fields.Selection(string='status',
        selection=[('draft', 'Draft'), ('open', 'Open'), ('done', 'Done'), ('cancel', 'Cancel')],
        related='do_id.state',
        default='draft')
    tanggal = fields.Date(string='Tanggal', compute='_hitung_tanggal', store=True, readonly=True)
    

    @api.multi
    def name_get(self):
        result = []
        for attendance in self:
            if not attendance.check_out:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s") % {
                    'empl_name': attendance.do_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                }))
            else:
                result.append((attendance.id, _("%(empl_name)s from %(check_in)s to %(check_out)s") % {
                    'empl_name': attendance.do_id.name,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_in))),
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(attendance, fields.Datetime.from_string(attendance.check_out))),
                }))
        return result

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            _logger.info('test : %s' % type(attendance.check_out))
            _logger.info('test2 : %s' % DEFAULT_SERVER_DATETIME_FORMAT)
            if attendance.check_out:
                # delta = datetime.strptime(attendance.check_out, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                #     attendance.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise exceptions.ValidationError(
                        _('"Check Out" time cannot be earlier than "Check In" time.'))

    @api.constrains('check_in', 'check_out', 'do_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['freight.attendance'].search([
                ('do_id', '=', attendance.do_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") % {
                    'empl_name': attendance.do_id.name,
                    'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(attendance.check_in))),
                })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['freight.attendance'].search([
                    ('do_id', '=', attendance.do_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ])
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the vehicle hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.do_id.name,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_out_attendances.check_in))),
                    })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['freight.attendance'].search([
                    ('do_id', '=', attendance.do_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") % {
                        'empl_name': attendance.do_id.name,
                        'datetime': fields.Datetime.to_string(
                            fields.Datetime.context_timestamp(
                                self,
                                fields.Datetime.from_string(
                                    last_attendance_before_check_out.check_in
                                    )
                                )
                            ), 
                        }
                        )

    @api.multi
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an attendance.'))

    @api.multi
    def auto_checkout(self):
        nocheckout = self.env['freight.attendance'].search(
            [('check_out', '=', False)])
        for line in nocheckout:
            line.check_out = fields.Datetime.now()


    def rekap_do(self):
        jam = datetime.now().time().hour + 7
        login_user = self.env['res.users'].search([('id', '=', self.env.uid)])
        if jam >= 0 and jam < 6 :
            kemarin = datetime.now()-timedelta(days=1)
            hari_ini = datetime.strftime(kemarin,'%Y-%m-%d')
        else:
            hari_ini = datetime.strftime(fields.Datetime.now(),'%Y-%m-%d')
            if login_user.shift.name == 'Shift 1' and jam >= 29 and jam <=31:  
                hari_ini = datetime.strftime(fields.Date.today()+timedelta(days=1),'%Y-%m-%d')

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
            """ % (hari_ini, self.env.user.gardu.id, self.env.user.shift.id))

        hasil = self.env.cr.fetchall()
        if hasil:
            usermessage = ''
            for baris in hasil:
                usermessage = usermessage + '%s/%s = %s <br>'%(baris[2],baris[3],baris[4])
            # raise UserError(usermessage)
            self.env.user.notify_info(usermessage,'Hasil Penerimaan hari ini', True)
            # return
            # wizard_form = self.env.ref('wk_wizard_messages.wizard_message_form', False)
            # view_id = self.env['wk.wizard.message']
            # partial_id = view_id.create({'text':usermessage}).id
            # print('lewat sini broo!! : %s' % partial_id)
            # return {
            #     'name':'Information',
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'wk.wizard.message',
            #     'res_id': partial_id,
            #     'view_id': wizard_form.id,
            #     'view_mode': 'form',
            #     'view_type': 'form',
            #     'target': 'current',
            # }

        else:
            self.env.user.notify_info('Belum ada penerimaan untuk saat ini',"Informasi", True)
            return
            
    def rekap_do_kiosK(self):
        jam = datetime.now().time().hour + 7
        login_user = self.env['res.users'].search([('id', '=', self.env.uid)])
        if jam >= 0 and jam < 6 :
            kemarin = datetime.now()-timedelta(days=1)
            hari_ini = datetime.strftime(kemarin,'%Y-%m-%d')
        else:
            hari_ini = datetime.strftime(fields.Datetime.now(),'%Y-%m-%d')
            if login_user.shift.name == 'Shift 1' and jam >= 29 and jam <=31:  
                hari_ini = datetime.strftime(fields.Date.today()+timedelta(days=1),'%Y-%m-%d')
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
            """ % (hari_ini, self.env.user.gardu.id, self.env.user.shift.id))
        hasil = self.env.cr.fetchall()
        result =[]
        if hasil:
            usermessage = ''
            for baris in hasil:
                data = {'Hasil':'%s/%s : %s'%(baris[2],baris[3], baris[4])};
                result.append(data);
            # raise UserError(usermessage)
            return result;

        else:
            return 

    @api.one
    @api.depends('check_in')
    def _hitung_tanggal(self):
        # print("Lewat sini")
        if self.check_in :
            # print('Shift : %s' % self.shift.name)
            if self.shift.name == 'Shift 3' :
                self.tanggal = self.check_in.strftime('%Y-%m-%d')
            else :
                self.tanggal = (self.check_in + timedelta(hours=1)).strftime('%Y-%m-%d')
            # print('Tanggal : %s/%s' % (self.check_in, self.tanggal))
        else :
            self.tanggal = False


class ResCompany(models.Model):
    _inherit = 'res.company'

    tenggat = fields.Integer(string='Tenggat Waktu (Bulan)')


class PrintDO(models.Model):
    _name = 'print.do'
    _description = 'Modul wizard cetak DO'

    name = fields.Char(string='Name')
    do1_id = fields.Many2one(comodel_name='delivery.order', string='DO 1')
    do2_id = fields.Many2one(comodel_name='delivery.order', string='DO 2')
    do3_id = fields.Many2one(comodel_name='delivery.order', string='DO 3')
    do4_id = fields.Many2one(comodel_name='delivery.order', string='DO 4')


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_ids = fields.One2many(comodel_name='res.users.pos', inverse_name='user_id', string='pos_ids')
    active_pos = fields.Many2one(comodel_name='pos.gardu', string='Pos saat ini', compute="_compute_pos")
    gardu = fields.Many2one(comodel_name='pos.gardu', string='Pos')
    shift = fields.Many2one(comodel_name='pos.shift', string='Shift')
    
    
    
    @api.multi
    def _compute_pos(self):
        sekarang = datetime.today()+timedelta(hours=7)
        dow = sekarang.weekday()
        # print(sekarang)
        # print(dow)
        self.active_pos = self.env['pos.gardu'].search([],limit=1) 
        return
    
    @api.model
    def get_users_login_shift(self, uid):
        login_user = self.env['res.users'].search([('id', '=',uid)])
        return login_user.shift.name;
        
    @api.model
    def get_users_login_pos(self, uid):
        login_user = self.env['res.users'].search([('id', '=',uid)])
        return login_user.gardu.name;
        

class ResUsersPos(models.Model):
    _name = 'res.users.pos'

    hari = fields.Selection(string='Hari', selection=[
        ('6', 'Minggu'),
        ('0', 'Senin'),
        ('1', 'Selasa'),
        ('2', 'Rabu'),
        ('3', 'Kamis'),
        ('4', "Jumat"),
        ('5', 'Sabtu'),
        ])
    jam_mulai = fields.Float(string='Jam mulai')
    jam_selesai = fields.Float(string='Jam selesai')
    pos = fields.Many2one(comodel_name='pos.gardu', string='Pos')
    user_id = fields.Many2one(comodel_name='res.users', string='User Id')
    


class PosGardu(models.Model):
    _name = 'pos.gardu'

    name = fields.Char(string='Pos')
    

class PosShift(models.Model):
    _name = 'pos.shift'
    _description = 'Pos Shift'

    name = fields.Char(string='Name')


