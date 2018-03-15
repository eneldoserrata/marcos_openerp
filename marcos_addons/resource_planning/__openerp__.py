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

{
    'name': 'Facilitates resource planning',
    'version': '1.0',
    'category': 'Dependency',
    'description': """This module offers functions for coordinating several
    resources""",
    'author': 'Therp BV',
    'website': 'http://www.therp.nl',
    'depends': [
        'web_calendar',
        'resource',
               ],
    'init_xml': [],
    'update_xml': [
    ],
    'js': [
        'static/lib/dhtmlxScheduler/sources/dhtmlxscheduler.js',
        'static/lib/dhtmlxScheduler/sources/ext/dhtmlxscheduler_minical.js',
        'static/lib/dhtmlxScheduler/sources/ext/dhtmlxscheduler_units.js',
        'static/lib/dhtmlxScheduler/sources/ext/dhtmlxscheduler_limit.js',
        'static/lib/dhtmlxScheduler/sources/ext/dhtmlxscheduler_timeline.js',
        'static/src/js/resource_planning.js',
        ],
    'css': [
        'static/lib/dhtmlxScheduler/codebase/dhtmlxscheduler_glossy.css',
        'static/src/css/resource_planning.css',
        ],
    'data': [
        ],
    'qweb' : [
        'static/src/xml/*.xml',
        ],
    'installable': True,
    'active': False,
}
