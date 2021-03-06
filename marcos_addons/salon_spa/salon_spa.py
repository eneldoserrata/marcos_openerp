# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Jean Ventura (<http://venturasystems.net>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta, time

from openerp.addons.base_status.base_state import base_state
from openerp.tools.translate import _
from openerp.osv.orm import Model, except_orm
from openerp.osv import fields
from openerp.addons.resource_planning.resource_planning import resource_planning


#order is important here. resource_planning has to come first
class appointment(resource_planning, base_state, Model):
    _name = 'salon.spa.appointment'

    _resource_fields = ['employee_id', 'space_id']

    _date_field = 'start'

    _duration_field = 'duration'

    _columns = {
            'name': fields.char('Nombre', size=128),
            'start': fields.datetime('Inicio', required=True),
            'duration': fields.float(u'Duración', required=True),
            'price': fields.float(u'Precio'),
            'employee_id': fields.many2one(
                'hr.employee', 'Empleado', required=True),
            'client_id': fields.many2one(
                'res.partner', 'Cliente',
                domain=[('supplier', '=', False)], required=True,),
            'service_id': fields.many2one(
                'salon.spa.service', 'Servicio', required=True),
            'space_id': fields.many2one(
                'salon.spa.space', 'Espacio', required=True),
            'state': fields.selection([('draft', 'Reservada'),
                                       ('pending', 'En Espera'),
                                       ('open', 'Confirmada'),
                                       ('done', 'Concluida'),
                                       ('cancel', 'Cancelada')],
                                       string='Estado', size=16, readonly=True,
                                       track_visibility='onchange',
                                       help="Este estado marca la cita como:\
                                             'Reservada' cuando se crea.\
                                             'En Espera' el dia de la cita,\
                                             y el cliente no ha llegado.\
                                             'Confirmada' el cliente llego.\
                                             'Concluida' la cita concluida.\
                                             'Cancelada' no-show, etc."),
            'notes': fields.text('Notas'),
            'active': fields.boolean('Activo', required=False),
            'order_line_id': fields.many2one(
                'pos.order.line', 'Registro de Venta')
            }

    def _last_appointment_client(self, cr, uid, context=None):
        """
        Search for the last appointment created for today and return
        it's client id.

        """

        today = datetime.strftime(datetime.today(), "%Y-%m-%d %H:%M:%S")
        day_start, day_end = self._day_start_end_time(today)
        appt_id = self.search(cr, uid,
                    [('start', '>=', day_start),
                     ('start', '<=', day_end)],
                order='create_date desc', context=context)
        if appt_id:
            appt_obj = self.browse(cr, uid, appt_id[0], context=context)
            return appt_obj.client_id.id

    def _round_time(self, dt=None, round_to=60):
       """
       Round a datetime object to any time laps in seconds
       dt : datetime.datetime object, default now.
       round_to : Closest number of seconds to round to, default 1 minute.
       Author: Thierry Husson 2012 - Use it as you want but don't blame me.

       """

       if dt == None : dt = datetime.now()
       seconds = (dt - dt.min).seconds
       # // is a floor division, not a comment on following line:
       rounding = (seconds + round_to / 2) // round_to * round_to
       return dt + timedelta(0, rounding - seconds, -dt.microsecond)

    def _next_available_date(self, cr, uid, context=None):
        """
        Search the closest available datetime for an appointment
        (duration not considered)

        """

        # Round to next five minute interval
        date_start = self._round_time(round_to=60 * 5) + timedelta(minutes=5)
        # TODO use correct timezone to compare with salon.spa.schedule
        # sched = schedule
        date = datetime.strftime(date_start.date(), "%Y-%m-%d")
        sched_id = self.pool.get('salon.spa.schedule').\
                search(cr, uid, [('date', '=', date)], context=context)
        if sched_id:
            sched_obj = self.pool.get('salon.spa.schedule').\
                    browse(cr, uid, sched_id[0], context=context)
            date_closing = date_start.replace(hour=int(sched_obj.hour_end), minute=00, second=00)
            minutes_till_closing = (date_closing - date_start).seconds / 60
            date_end = date_start + timedelta(minutes=30)  # 30 minutes = default appt length
            for minutes in range(5, minutes_till_closing, 5):
                if date_start.hour >= sched_obj.hour_start \
                    and date_start.hour < sched_obj.hour_end:
                    date_end = date_start + timedelta(minutes=30)  # 30 minutes = default appt length
                    if not self.search(cr, uid,
                        [('start', '>=', self._datetime_to_string(date_start)),
                         ('start', '<=', self._datetime_to_string(date_end))],
                        context=context):
                        return self._datetime_to_string(date_start)
                date_start = date_end + timedelta(minutes=minutes)
        return None

    _defaults = {
            'client_id': _last_appointment_client,
            'start': _next_available_date,
            'state': 'draft',
            'active': True
        }

    # appt = appointment
    def onchange_appointment_service(self, cr, uid, ids, service_id, employee_id, context=None):
        """
        Validates if resources (space and employee) are available for the
        time frame selected.

        Assigns first available resource and sets proper domain.

        Assigns prices and duration according to service.

        """

        if service_id:
            service_obj = self.pool.get('salon.spa.service').\
                    browse(cr, uid, service_id, context=context)
            start_date, duration = context['start_date'], service_obj.duration,

            # Space availability validation
            space_ids = []
            for space in service_obj.space_ids:
                space_available = self.check_resource_availability(cr, uid, ids,\
                                    'space_id', space.id, start_date, \
                                    duration, context)
                if space_available:
                    space_ids.append(space.id)
            if space_ids:
                assigned_space = space_ids[0]
            else:
                assigned_space = None

            # Employee availability validation
            employee_obj = self.pool.get('hr.employee').\
                    search(cr, uid, [('service_ids', 'in', service_id)], context=context)
            employee_ids = []
            for employee in employee_obj:
                employee_available = self.check_resource_availability(cr, uid, ids,\
                                    'employee_id', employee, start_date, \
                                    duration, context)
                if employee_available:
                    employee_available = self.check_employee_availability(cr, uid, ids,\
                            employee, start_date, duration, context)
                    if employee_available:
                        employee_ids.append(employee)
            if employee_ids:
                assigned_employee = employee_id if employee_id in employee_ids else employee_ids[0]
            else:
                assigned_employee = None

            return {
                    'value': {'duration': duration,
                              'price': service_obj.service.list_price,
                              'space_id': assigned_space,
                              'employee_id': assigned_employee
                        },
                    'domain': {'employee_id': [('id', 'in', employee_ids)],
                               'space_id': [('id', 'in', space_ids)]
                        },
                   }
        return {'value':
                    {'price': 0,
                     'space_id': None,
                     'duration': 0,
                     'employee_id': None,
                     }
                }

    def onchange_appointment_start(self, cr, uid, ids,
            employee_id, start, duration, context=None):
        """
        Validates appointment when start date changes.

        """

        if employee_id:
            employee_available = self.check_employee_availability(cr, uid, ids,\
                    employee_id, start, duration, context=context)
            if not employee_available:
                self._raise_unavailable(cr, uid, 'hr.employee', employee_id, context)
        return {}

    def case_open(self, cr, uid, ids, context=None):
        """
        Overwrite of base state case open to only change state.
        (Just like the rest of the states)

        Opens case

        """

        values = {'active': True}
        return self.case_set(cr, uid, ids, 'open', values, context=context)

    def _to_datetime(self, date):
        """
        Get a string date in 'YYYY-mm-dd HH:MM:SS' format.
        Return a datetime object of said date.

        """

        return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    def _datetime_to_string(self, date):
        """
        Get a datetime object.
        Return a string date in 'YYYY-mm-dd HH:MM:SS' format
        of said date.

        """

        return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

    def _day_start_end_time(self, date):
        """
        Get a string date in 'YYYY-mm-dd HH:MM:SS' format.
        Return 2 string dates corresponding to the starting and ending hours
        of the day of the original date.

        """

        day_start = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0)
        day_start = datetime.strftime(day_start, "%Y-%m-%d %H:%M:%S")
        day_end = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(hour=23, minute=59, second=59)
        day_end = datetime.strftime(day_end, "%Y-%m-%d %H:%M:%S")
        return day_start, day_end

    def _validate_past_date(self, date):
        if self._to_datetime(date) < datetime.today():
            raise except_orm(_('Error'), _("Can't create an event in the past."))
        return True

    def _raise_unavailable(self, cr, uid, model, ids, context=None):
        model_obj = self.pool.get(model).\
                browse(cr, uid, ids, context=context)
        raise except_orm(_('Error'), _('%s is not '
            'available at this time!') % (
            model_obj.name))

    def _check_client_available(self, cr, uid, ids, client_id, start_date, duration, context):
        client_obj = self.pool.get('res.partner').\
                browse(cr, uid, client_id, context=context)
        # TODO REFACTOR Break and Lunch as hardcoded values
        if client_obj.name not in ['Break', 'Lunch']:
            if not self.check_resource_availability(cr, uid, ids,
                    'client_id', client_id, start_date, duration, context):
                self._raise_unavailable(cr, uid, 'res.partner', client_id, context)
        return True

    def _get_order_ids_client_day(self, cr, uid, client_id, date, context=None):
        day_start, day_end = self._day_start_end_time(date)
        return self.pool.get('pos.order').\
                search(cr, uid, [('date_order', '>=', day_start),
                                 ('date_order', '<=', day_end),
                                 ('state', '!=', 'invoiced'),
                                 ('partner_id', '=', client_id)],
                       context=context)

    def _create_update_order_client_day(self, cr, uid, client_id, date, appt_id, service_obj, appt_obj, context=None):
        """
        Creates pos.order for a client in an specified day with an pos.order.line
        that corresponds to the appointment/service.

        If the pos.order exists, it just adds the pos.order.line.

        """

        if not context:
            context = {}
        order_ids = self._get_order_ids_client_day(cr, uid, client_id, date, context)
        # Order creation/modification
        if order_ids:
            order_id = order_ids[0]
        else:  # create it
            session_id = self.pool.get("pos.session").search(cr, uid,
                [('user_id', '=', uid),
                 ('state', '=', 'opened')],
                context=context)
            if session_id:
                context['empty_order'] = True
                order_id = self.pool.get('pos.order').create(cr, uid, {
                    'partner_id': client_id,
                    'date_order': date,
                    'session_id': session_id[0],
                    # TODO get correct pricelist_id
                    'pricelist_id': 1,
                    'parent_return_order': '',
                    }, context=context)
            else:
                raise except_orm(_('Error'), _('No cashbox available.'))
        # add service to order
        order_line_id = self.pool.get('pos.order.line').create(cr, uid, {
                        'order_id': order_id,
                        'name': service_obj.service.name,
                        'product_id': service_obj.service.id,
                        'price_unit': service_obj.service.list_price,
                        'appointment_id': appt_id,
                        'employee_id': appt_obj.employee_id.id
                        })
        # Update appointment with proper order line
        appt_obj = self.browse(cr, uid, [appt_id], context=context)[0]
        appt_obj.write({'order_line_id': order_line_id})

        # TODO Limpiar facturas cuando se elimina un appt o servicio

        return True

    def action_check_in(self, cr, uid, ids, context=None):
        """
        Changes the state of all appointments of the client to 'open'
        and creates an pos.order for each one.

        """

        appt_obj = self.browse(cr, uid, ids[0], context=context)
        day_start, day_end = self._day_start_end_time(appt_obj.start)
        appt_ids = self.search(cr, uid,
                [('start', '>=', day_start),
                 ('start', '<=', day_end),
                 ('state', 'in', ['pending']),
                 ('client_id', '=', appt_obj.client_id.id)],
                context=context)
        for appt_id in appt_ids:
            appt_obj = self.browse(cr, uid, [appt_id], context=context)[0]
            appt_obj.case_open()
            if not self._create_update_order_client_day(cr, uid,\
                    appt_obj.client_id.id, appt_obj.start, appt_id, appt_obj.service_id, appt_obj, context):
                raise except_orm(_('Error'), _('Error creating/updating pos.order or pos.order.line.'))
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        appt_obj = self.browse(cr, uid, ids[0], context=context)
        if appt_obj.order_line_id:
            del_order_line = self.pool.get('pos.order.line').\
                    browse(cr, uid, appt_obj.order_line_id.id, context=context)
            if del_order_line:
                del_order_line.write({'appointment_id': None})
                del_order_line.unlink()

        self.case_cancel(cr, uid, ids)
        return True

    def action_view_pos_order(self, cr, uid, ids, context=None):
        """
        This function returns an action that displays existing orders
        of the client for the same day of this appointment.
        It can either be in a list,
        or in a form view if there is only one invoice to show.

        """

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'point_of_sale', 'action_pos_pos_form')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]

        # get orders for the client/day (of appointment)
        # appt_obj = self.browse(cr, uid, ids, context=context)[0]
        # order_ids = self._get_order_ids_client_day(cr, uid, appt_obj.client_id.id, appt_obj.start, context)
        appt_obj = self.browse(cr, uid, ids, context=context)[0]
        order_ids = self.pool.get('pos.order').search(cr, uid, [('id','=',appt_obj.order_line_id.order_id.id)])
        # result['domain'] = "[('id','=',[" + ','.join(map(str, order_ids)) + "])]"

        # change to form view if theirs only one order for the client/day
        if len(order_ids) == 1:
            result['views'] = [(False, 'form')]
            result['res_id'] = order_ids and order_ids[0] or False
        return result

    def check_resource_availability(self, cr, uid, ids,
            resource_type, resource, start_date, duration, context=None):
        """
        Validates that the specified resource_type/resource is available.

        Either end_date or duration is required. If neither, will return False.

        """

        # TODO REFACTOR all validations related to resource availability can be
        # checked with self._assert_availability/self._check_availability.
        # (Employee work schedule doesn't fit here,
        #  unless modifications are done to those methods.)
        day_start, day_end = self._day_start_end_time(start_date)
        start_date = self._to_datetime(start_date)
        end_date = start_date + timedelta(hours=duration)

        appt_ids = self.pool.get('salon.spa.appointment').\
                search(cr, uid, [('start', '>=', day_start),
                                 ('start', '<=', day_end),
                                 ('state', '!=', 'cancel'),
                                 ('id', '!=', ids),
                                 (resource_type, '=', resource)],
                        context=context)

        for appt in appt_ids:
            appt_obj = self.pool.get('salon.spa.appointment').\
                    browse(cr, uid, appt, context=context)
            appt_start_date = datetime.strptime(appt_obj.start, '%Y-%m-%d %H:%M:%S')
            appt_end_date = appt_start_date + timedelta(hours=appt_obj.duration)
            if  (start_date >= appt_start_date and start_date < appt_end_date) \
                or (end_date > appt_start_date and end_date <= appt_end_date):
                return False
        return True

    def check_employee_availability(self, cr, uid, ids,
            employee_id, start_date, duration, context=None):
        """
        Validates that the employee is able to work at the specified time.

        Either end_date or duration is required. If neither, will return False.

        """

        start_date = self._to_datetime(start_date)
        end_date = start_date + timedelta(hours=duration)

        start_date = fields.datetime.context_timestamp(
                cr, uid, start_date, context=context)
        end_date = fields.datetime.context_timestamp(
                cr, uid, end_date, context=context)

        appt_start_hour = start_date.hour
        appt_end_hour = end_date.hour + (end_date.minute / 60)  # float format

        date = datetime.strftime(start_date.date(), "%Y-%m-%d")
        sched_id = self.pool.get('salon.spa.schedule').\
                search(cr, uid, [('date', '=', date)])
        sched_obj = self.pool.get('salon.spa.schedule').\
                browse(cr, uid, sched_id, context=context)
        if sched_obj:
            for line in sched_obj[0].schedule_line_ids:
                if line.employee_id.id == employee_id:
                    if appt_start_hour >= line.hour_start \
                        and appt_end_hour <= line.hour_end \
                        and not line.missing:
                        return True
        return False

    def unlink(self, cr, uid, ids, context=None):
        """
        Avoid unlinking of appointments in 'done' state.

        """

        if type(ids) is not list: ids = [ids]
        for appt_id in list(ids):
            appt_obj = self.pool.get('salon.spa.appointment').\
                    browse(cr, uid, appt_id, context=context)
            if appt_obj.state == 'done':
                raise except_orm(_('Error'), _("Appointment is done/paid, it can't be deleted."))
        return super(appointment, self).unlink(cr, uid, ids, context)

    def write(self, cr, uid, ids, vals, context=None):
        # keys in vals correspond with fields that have changed
        # Get values previous to save
        # prev_appt holds state of appt previous to save
        appt_obj = self.pool.get('salon.spa.appointment').\
                browse(cr, uid, ids[0], context=context)

        # 'done' and 'cancel' appointments mustn't be modified
        if appt_obj.state == 'done':
            raise except_orm(_('Error'), _("Appointment is done/paid, it can't be modified."))
        elif appt_obj.state == 'cancel':
            raise except_orm(_('Error'), _("Appointment was cancelled, it can't be modified."))

        prev_appt = {'employee_id': appt_obj.employee_id.id,
                     'start': appt_obj.start,
                     'client_id': appt_obj.client_id.id,
                     'duration': appt_obj.duration,
                     'service_id': appt_obj.service_id.id,
                     }
        #if vals.get('start', False):
        #    self._validate_past_date(vals.get('start', False) or prev_appt['start'])

        service_obj = self.pool.get('salon.spa.service').\
                browse(cr, uid, vals.get('service_id', False) or prev_appt['service_id'], context=context)
        # store read-only fields
        vals['price'] = service_obj.service.list_price
        vals['duration'] = service_obj.duration

        # Check if client is available for service.
        self._check_client_available(cr, uid, ids,
                vals.get('client_id', False) or prev_appt['client_id'],
                vals.get('start', False) or prev_appt['start'],
                vals.get('duration', False) or prev_appt['duration'], context)

        result = super(appointment, self).write(cr, uid, ids, vals, context)

        # current_appt holds final state of appt
        # (Take all values not changed from previously saved appt)
        current_appt = {}
        for key, val in vals.iteritems():
            current_appt[key] = val
        for key, val in prev_appt.iteritems():
            if key not in current_appt:
                current_appt[key] = val

        # Check if employee is available and assigned to service.
        if vals.get('employee_id', False):
            employee_obj = self.pool.get('hr.employee').\
                    browse(cr, uid, current_appt['employee_id'],
                           context=context)
            service_ids = []
            for service in employee_obj.service_ids:
                service_ids.append(service.id)
            if current_appt['service_id'] not in service_ids:
                raise except_orm(_('Error'), _('%s is not '
                    'assigned to work with %s!') % (
                    employee_obj.name,
                    service_obj.service.name))
            if not self.check_resource_availability(cr, uid, ids,
                    'employee_id', current_appt['employee_id'],
                    current_appt['start'], current_appt['duration'], context):
                self._raise_unavailable(cr, uid, 'hr.employee', current_appt['employee_id'], context)

        # Check if space is available
        if vals.get('space_id', False):
            if not self.check_resource_availability(cr, uid, ids,
                    'space_id', current_appt['space_id'],
                    current_appt['start'], current_appt['duration'], context):
                self._raise_unavailable(cr, uid, 'salon.spa.space', current_appt['space_id'], context)

        # Duration changes if service is modified
        if vals.get('duration', False) or vals.get('employee_id', False):
            # Validate employee work schedule
            employee_available = self.check_employee_availability(cr, uid, ids,
                    current_appt['employee_id'], current_appt['start'],
                    current_appt['duration'], context)
            if not employee_available:
                self._raise_unavailable(cr, uid, 'hr.employee', current_appt['employee_id'], context)

        # If one of the orders related fields changes
        # (client_id, start, service_id), delete order line for appt.
        # Later an order is created or modificed with the new info.
        if appt_obj.state in ['open'] \
            and (vals.get('client_id', False) \
                or vals.get('start', False) \
                or vals.get('service_id', False) \
                ):
            if current_appt['client_id'] != prev_appt['client_id'] \
                or datetime.strptime(current_appt['start'], '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0) \
                   != datetime.strptime(prev_appt['start'], '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0) \
                or current_appt['service_id'] != prev_appt['service_id']:
                order_line_obj = self.pool.get('pos.order.line').\
                        search(cr, uid, [('appointment_id', '=', ids[0])],
                               context=context)
                del_order_line = self.pool.get('pos.order.line').\
                        unlink(cr, uid, order_line_obj[0], context=context)
                if not del_order_line:
                    raise except_orm(_('Error'), _('Error removing pos.order.line.'))
                if not self._create_update_order_client_day(cr, uid, current_appt['client_id'], current_appt['start'], ids[0], service_obj, context):
                    raise except_orm(_('Error'), _('Error creating/updating pos.order or pos.order.line.'))
        return result

    def create(self, cr, uid, vals, context=None):
        #self._validate_past_date(vals['start'])

        service_obj = self.pool.get('salon.spa.service').\
                browse(cr, uid, vals['service_id'], context=context)
        # store read-only fields
        vals['price'] = service_obj.service.list_price
        vals['duration'] = service_obj.duration
        ids = vals

        # Validate employee work schedule
        employee_available = self.check_employee_availability(cr, uid, ids,\
                vals['employee_id'], vals['start'], \
                vals['duration'], context)
        if not employee_available:
            self._raise_unavailable(cr, uid, 'hr.employee', vals['employee_id'], context)

        id = super(appointment, self).create(cr, uid, vals, context)

        # Check if client is available for service.
        self._check_client_available(cr, uid, id,
                vals.get('client_id', False), vals.get('start', False),
                vals.get('duration', False), context)

        # TODO REFACTOR Break and Lunch as hardcoded values
        if service_obj.name not in ['Break', 'Lunch']:
            self.case_pending(cr, uid, [id])
        return id


class service(Model):
    _inherit = 'resource.resource'

    _name = 'salon.spa.service'

    _columns = {
            'service': fields.many2one(
                'product.product',
                'Nombre',
                domain=[('type', '=', 'service')],
                required=True),
            'duration': fields.float('Tiempo', required=True),
            'categ_id': fields.char('Categoria', required=True),
            'instructions': fields.text('Instrucciones', translate=True),
            'space_ids': fields.many2many(
                'salon.spa.space',
                'service_space_rel',
                'service_id', 'space_id',
                'Espacios Permitidos'),
            }

    _defaults = {
            'resource_type': 'material',
            }

    def onchange_service_service(self, cr, uid, ids, service, context=None):
        if service:
            product_obj = self.pool.get('product.product').\
                    browse(cr, uid, service, context=context)
            return {'value':
                        {'name': product_obj.name,
                         'categ_id': product_obj.categ_id.id,
                             }
                   }
        return {}


class space(Model):
    _inherit = 'resource.resource'

    _name = 'salon.spa.space'

    _defaults = {
            'resource_type': 'material',
            }


class schedule(Model):
    _name = 'salon.spa.schedule'

    _order = 'date desc'

    _columns = {
            'date': fields.date('Date', required=True),
            'hour_start': fields.float(u'Starting Hour', required=True),
            'hour_end': fields.float(u'Ending Hour', required=True),
            'schedule_line_ids': fields.one2many('salon.spa.schedule.line', 'schedule_id', 'Schedule Lines'),
            }

    def create(self, cr, uid, vals, context=None):
        if self.pool.get('salon.spa.schedule').search(cr, uid, [('date', '=', vals.get('date'))], context=context):
            raise except_orm(_('Error'), _("Can't create schedule with this date. Duplicate exists."))
        id = super(schedule, self).create(cr, uid, vals, context)
        return id

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('date')\
            and self.pool.get('salon.spa.schedule').\
                    search(cr, uid, [('date', '=', vals.get('date'))], context=context):
            raise except_orm(_('Error'), _("Can't change schedule to this date. Duplicate exists."))
        result = super(schedule, self).write(cr, uid, ids, vals, context)
        return result


class schedule_line(Model):
    _name = 'salon.spa.schedule.line'

    _order = 'hour_start, employee_id'

    _columns = {
            'employee_id': fields.many2one(
                'hr.employee', 'Employee', required=True),
            'hour_start': fields.float(u'Starting Hour', required=True),
            'hour_end': fields.float(u'Ending Hour', required=True),
            'missing': fields.boolean('Missing', required=False),
            'schedule_id': fields.many2one(
                'salon.spa.schedule', 'Schedule', required=True),
            }

    _defaults = {
            'missing': False,
            }

    def _range_start_end_time(self, date, hour_start, hour_end):
        """
        Get a string date in 'YYYY-mm-dd HH:MM:SS' format.
        Return 2 string dates corresponding to the starting and ending hours
        received in parameters (as integers).

        """

        day_start = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(hour=hour_start, minute=0, second=0)
        day_start = datetime.strftime(day_start, "%Y-%m-%d %H:%M:%S")
        day_end = datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(hour=hour_end, minute=0, second=0)
        day_end = datetime.strftime(day_end, "%Y-%m-%d %H:%M:%S")
        return day_start, day_end

    def _get_appointments_in_range(self, cr, uid, employee_id, start_time, end_time, context=None):
        """
        Get two datetime string ranges and determine if an appointment exists inside.

        """

        return self.pool.get('salon.spa.appointment').\
                search(cr, uid, [('start', '>=', start_time),
                                 ('start', '<=', end_time),
                                 ('state', '!=', 'cancel'),
                                 ('employee_id', '=', employee_id)],
                        context=context)

    # REFACTOR. This is in two classes.
    def _to_datetime(self, date):
        """
        Get a string date in 'YYYY-mm-dd HH:MM:SS' format.
        Return a datetime object of said date.

        """

        return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    def _validate_start_end(self, hour_start, hour_end):
        if hour_end <= hour_start:
            raise except_orm(_('Error'), _("Ending time is greater or equal to starting time, please fix."))
        return True

    def create(self, cr, uid, vals, context=None):
        """
        Modified to add validation to avoid assigning start/end outside schedule range.

        """

        hour_start = vals.get('hour_start')
        hour_end = vals.get('hour_end')
        self._validate_start_end(hour_start, hour_end)

        sched_obj = self.pool.get('salon.spa.schedule').browse(cr, uid, vals.get('schedule_id'), context=context)
        if sched_obj.hour_start > hour_start\
                or sched_obj.hour_end < hour_end:
            raise except_orm(_('Error'), _("Start and/or end times are outside of allowed values. Can't create."))
        # Create schedule.line before appointment
        id = super(schedule_line, self).create(cr, uid, vals, context)

        # Create lunch break
        time_float = (hour_end + hour_start) / 2.0
        # TODO fix timezone problem
        time_tz = time_float + 4
        hours = int(time_tz)
        minutes = int((time_tz - hours) * 60)
        time_str = str(time(hour=hours, minute=minutes))
        start = sched_obj.date + ' ' + time_str
        client_id = self.pool.get('res.partner').\
                search(cr, uid, [('name', '=', 'Break')], context=context)
        service_id = self.pool.get('salon.spa.service').\
                search(cr, uid, [('name', '=', 'Lunch')], context=context)
        space_id = self.pool.get('salon.spa.space').\
                search(cr, uid, [('name', '=', 'Libre')], context=context)
        # To get service information.
        service_obj = self.pool.get('salon.spa.service').\
                browse(cr, uid, client_id[0], context=context)
        values = {'client_id': client_id[0],
                  'start': start,
                  'service_id': service_id[0],
                  'duration': service_obj.duration,
                  'price': service_obj.service.list_price,
                  'space_id': space_id[0],
                  'employee_id': vals.get('employee_id')
                  }
        self.pool.get('salon.spa.appointment').create(cr, uid, values)

        return id

    def write(self, cr, uid, ids, vals, context=None):
        """
        Modified to add validations:

        salon.spa.schedule: avoid assigning start/end outside schedule range.
        salon.spa.appointment: avoid assigning start/end times outside all appointment range.

        """

        hour_start = vals.get('hour_start')
        hour_end = vals.get('hour_end')
        missing = vals.get('missing')

        sched_line_obj = self.pool.get('salon.spa.schedule.line').browse(cr, uid, ids[0], context=context)
        self._validate_start_end(hour_start or sched_line_obj.hour_start,
                                 hour_end or sched_line_obj.hour_end)

        if hour_start or hour_end or missing:
            sched_obj = self.pool.get('salon.spa.schedule').browse(cr, uid, sched_line_obj.schedule_id.id, context=context)
            if (hour_start and sched_obj.hour_start > hour_start)\
                or (hour_end and sched_obj.hour_end < hour_end):
                raise except_orm(_('Error'), _("Start and/or end times are outside of allowed values. Can't update."))

            date = datetime.strptime(sched_obj.date, '%Y-%m-%d')
            start_time, end_time = self._range_start_end_time(str(date),
                                                            int(sched_line_obj.hour_start),
                                                            int(sched_line_obj.hour_end))
            appt_ids = self._get_appointments_in_range(cr, uid, sched_line_obj.employee_id.id, start_time, end_time, context=context)
            if appt_ids and missing:
                raise except_orm(_('Error'), _("An employee reported as missing has existing appointment(s) for this day,"
                                               " please cancel or move the appointment(s) before saving."))
            for appt_id in appt_ids:
                appt_obj = self.pool.get('salon.spa.appointment').browse(cr, uid, appt_id, context=context)
                appt_start = self._to_datetime(appt_obj.start)
                appt_end = appt_start + timedelta(hours=appt_obj.duration)
                appt_start = appt_start.hour + (float(appt_start.minute) / 60)  # float format
                appt_end = appt_end.hour + (float(appt_end.minute) / 60)  # float format
                if (hour_start and appt_start < hour_start)\
                    or (hour_end and appt_end > hour_end):
                    raise except_orm(_('Error'), _("Start or end time is outside of allowed values. Can't update."))

        result = super(schedule_line, self).write(cr, uid, ids, vals, context)
        return result

    def unlink(self, cr, uid, ids, context=None):
        """
        Modified to add validation to avoid unlink with appointments in range.

        """

        sched_line_obj = self.pool.get('salon.spa.schedule.line').browse(cr, uid, ids[0], context=context)
        hour_start = sched_line_obj.hour_start
        hour_end =  sched_line_obj.hour_end
        sched_obj = self.pool.get('salon.spa.schedule').browse(cr, uid, sched_line_obj.schedule_id.id, context=context)
        date = datetime.strptime(sched_obj.date, '%Y-%m-%d')
        start_time, end_time = self._range_start_end_time(str(date),
                                                        int(hour_start),
                                                        int(hour_end))
        appt_exists = self._get_appointments_in_range(cr, uid, sched_line_obj.employee_id.id, start_time, end_time, context=context)
        if appt_exists:
            raise except_orm(_('Error'), _("A schedule was removed for an employee with appointment(s) assign,"
                                           " please cancel or remove the appointment(s) before deleting."))
        return super(schedule_line, self).unlink(cr, uid, ids, context)
