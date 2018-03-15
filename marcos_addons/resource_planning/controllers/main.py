# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Therp BV (<http://therp.nl>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.web import http as openerpweb
from openerp.modules.registry import RegistryManager


class resource_planning(openerpweb.Controller):
    _cp_path = "/resource_planning"
    
    @openerpweb.jsonrequest
    def resource_fields(self, req, model):
        '''Return list of resource fields'''
        pool = RegistryManager.get(req.session._db)
        model_obj = pool.get(model)
        return getattr(model_obj, '_resource_fields', [])

    @openerpweb.jsonrequest
    def get_leaves(self, req, model, date_from, date_to):
        '''Return dictionary of leaves with date (day) as key'''
        # TODO This is returning an error when model = crm.meeting. Why?
        # return req.session.model(model).get_leaves(date_from, date_to)
        return None
