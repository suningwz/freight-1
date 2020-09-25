# -*- coding: utf-8 -*-
from odoo import http

# class Freight(http.Controller):
#     @http.route('/freight/freight/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/freight/freight/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('freight.listing', {
#             'root': '/freight/freight',
#             'objects': http.request.env['freight.freight'].search([]),
#         })

#     @http.route('/freight/freight/objects/<model("freight.freight"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('freight.object', {
#             'object': obj
#         })