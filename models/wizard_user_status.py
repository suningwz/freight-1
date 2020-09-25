from odoo import api, fields, models


class WizardUserStatus(models.TransientModel):
    _name = 'wizard.user.status'
    _description = 'New Description'

    gardu = fields.Many2one(comodel_name='pos.gardu', string='Pos')
    shift = fields.Many2one(comodel_name='pos.shift', string='Shift')

    @api.multi
    def action_confirm(self):
        self.env.user.gardu = self.gardu
        self.env.user.shift = self.shift
        kiosk_url = self.env['ir.config_parameter'].get_param('kiosk.url')
        return {
            'type'      : 'ir.actions.act_url',
            'url'       : kiosk_url,
            'target'    : 'self',
        }

        # return {
        #     'name'      : 'Attendances',
        #     'tag'       : 'freight_attendances_kiosk_mode',
        #     'type'      : 'ir.actions.client',
        # }

    @api.multi
    def _get_status_gardu(self):
        return self.env.user.gardu.id

    @api.multi
    def _get_status_shift(self):
        return self.env.user.shift.id
    
    
