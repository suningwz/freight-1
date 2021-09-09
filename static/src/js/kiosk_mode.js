odoo.define('freight_attendance.kiosk_mode', function (require) {
    "use strict";
    
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Session = require('web.session');
    
    var QWeb = core.qweb;
    
    
    var KioskMode = AbstractAction.extend({
        events: {
            "click .o_freight_attendance_button_manual": function(){ this.do_action('freight.launched_wizard_do_cancel'); },
            "click .o_freight_attendance_button_rekap": function(){ this._rpc({
                model:'freight.attendance',
                method:'rekap_do',
                args:['test'],}); },
            "click .o_freight_attendance_button_logout": function(){ this.do_action('freight.launched_wizard_do_logout'); },
        },

        start: function () {
            var self = this;
            core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
            self.session = Session;

		this._rpc({
			model: 'res.users',
			method: 'get_users_login_pos',
			args: [Session.uid, ],
		}).then(function (data) {
			self.pos_name = data;
			console.log(data);
			self.$el.html(QWeb.render("FreightAttendanceKioskMode", {widget: self}));
		});

		this._rpc({
			model: 'res.users',
			method: 'get_users_login_shift',
			args: [Session.uid, ],
		}).then(function (shift) {
			self.shift_name = shift;
			console.log(shift);
			self.$el.html(QWeb.render("FreightAttendanceKioskMode", {widget: self}));
		});

            var def = this._rpc({
                    model: 'res.company',
                    method: 'search_read',
                    args: [[['id', '=', this.session.company_id]], ['name']],
                })
                .then(function (companies){
                    self.company_name = companies[0].name;
                    self.company_image_url = self.session.url('/web/image', {model: 'res.company', id: self.session.company_id, field: 'logo',});
                    self.$el.html(QWeb.render("FreightAttendanceKioskMode", {widget: self}));
                    self.start_clock();
                });
            // Make a RPC call every day to keep the session alive
            self._interval = window.setInterval(this._callServer.bind(this), (60*60*1000*24));
            return $.when(def, this._super.apply(this, arguments));
        },
    
        _onBarcodeScanned: function(barcode) {
            var self = this;
            core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
            this._rpc({
                    model: 'delivery.order',
                    method: 'attendance_scan',
                    args: [barcode, ],
                })
                .then(function (result) {
                    if (result.action) {
                        self.do_action(result.action);
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                        core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
                    }
                }, function () {
                    core.bus.on('barcode_scanned', self, self._onBarcodeScanned);
                });
        },
    
        start_clock: function() {
            this.clock_start = setInterval(function() {this.$(".o_freight_attendance_clock").text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));}, 500);
            // First clock refresh before interval to avoid delay
            this.$(".o_freight_attendance_clock").show().text(new Date().toLocaleTimeString(navigator.language, {hour: '2-digit', minute:'2-digit', second:'2-digit'}));
        },
    
        destroy: function () {
            core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
            clearInterval(this.clock_start);
            clearInterval(this._interval);
            this._super.apply(this, arguments);
        },
    
        _callServer: function () {
            // Make a call to the database to avoid the auto close of the session
            return ajax.rpc("/freight_attendance/kiosk_keepalive", {});
        },
    
    });
    
    core.action_registry.add('freight_attendance_kiosk_mode', KioskMode);
    
    return KioskMode;
    
    });
    
