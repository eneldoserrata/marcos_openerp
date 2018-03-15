// -*- encoding: utf-8 -*-
/*############################################################################
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
############################################################################*/

openerp.resource_planning = function(openerp)
{
    var _t = openerp.web._t;

    openerp.web_calendar.CalendarView.include({
        init: function(parent, dataset, view_id, options)
        {
            this.unit_resource_field = '';
            this.resource_fields={};
            return this._super(parent, dataset, view_id, options);
        },
        init_scheduler: function()
        {
            scheduler.skin = 'glossy';
            scheduler.config.now_date = Date.today();
            this._super();
            if(this.unit_resource_field)
            {
                this.$el.find('.oe_calendar [name=day_tab]').remove();
                this.$el.find('.oe_calendar [name=unit_tab]').wrapInner(
                        _t('Day'));
                this.$el.find('.oe_calendar [name=timeline_tab]').wrapInner(
                        _t('Timeline'));
            }
            else
            {
                this.$el.find('.oe_calendar [name=unit_tab]').remove();
                this.$el.find('.oe_calendar [name=timeline_tab]').remove();
            }
        },
        load_calendar: function(data)
        {
            var self = this;
            var super_func = _.bind(this._super, this)
            openerp.session.rpc('/resource_planning/resource_fields',
                {
                    model: self.dataset.model,
                }).then(
                function(results)
                {
                    _(results).each(function(resource_field)
                        {
                            if(!self.unit_resource_field)
                            {
                                self.unit_resource_field = resource_field;
                            }
                            self.resource_fields[resource_field] = data.fields[resource_field] ? data.fields[resource_field].string : resource_field;
                        });
                }).then(
                function()
                {
                    super_func(data);
                })
            return this.has_been_loaded;
        },
        update_range_dates: function(date)
        {
            switch(scheduler._mode ? scheduler._mode : this.mode || 'week')
            {
                case 'day':
                case 'unit':
                    this.range_start = date.clone().clearTime();
                    this.range_stop = this.range_start.clone().clearTime().addDays(1).addSeconds(-1);
                    break;
                case 'week':
                    this.range_start = date.clone().setWeek(date.getWeek());
                    this.range_stop = this.range_start.clone().addWeeks(1).addSeconds(-1);
                    break;
                default:
                    this._super(date);
            }
        },
        view_changed: function(mode, date)
        {
            this.$el.find('.oe_calendar').removeClass('oe_cal_day oe_cal_week oe_cal_month').addClass('oe_cal_' + mode);
            if(((this.old_mode && mode != this.old_mode) || !date.between(this.range_start, this.range_stop)) && this.last_search && this.last_search.length)
            {
                this.update_range_dates(date);
                this.ranged_search();
            }
            this.ready.resolve();
            this.old_mode=mode;
        },
        get_range_domain: function()
        {
            var format = openerp.web.date_to_str, domain = this.last_search[0].slice(0);
            domain.unshift([this.date_start, '>=', format(this.range_start.clone())]);
            domain.unshift([this.date_start, '<=', format(this.range_stop.clone())]);
            return domain;
        },
        events_loaded: function(events, fn_filter, no_filter_reload)
        {
            if($.isEmptyObject(this.resource_fields))
            {
                return this._super(events, fn_filter, no_filter_reload);
            }

            var self = this;

            var filter_values = jQuery.extend({}, this.resource_fields);
            for(var field in filter_values)
            {
                filter_values[field] = {};
            }
            if(this.color_field)
            {
                filter_values[this.color_field] = {};
            }

            var calendar_events=[]
            for(var e = 0; e < events.length; e++)
            {
                events[e].textColor = '#000';
                for(var field in filter_values)
                {
                    field_value = (typeof events[e][field] === 'object') ? events[e][field][0] : events[e][field];
                    field_label = (typeof events[e][field] === 'object') ? events[e][field][1] : events[e][field];
                    if(field_value && !filter_values[field][field_value])
                    {
                        filter_values[field][field_value]={
                            value: field_value,
                            label: field_label,
                            color: 'inherit',
                            textColor: 'inherit',
                        };
                    }
                    if(field == self.color_field)
                    {
                        events[e].color = filter_values[field][field_value].color = self.get_color(field_value);
                        events[e].textColor = filter_values[field][field_value].textColor = '#fff';
                    }
                }
                if(typeof(fn_filter) === 'function' && !fn_filter(events[e]))
                {
                    continue;
                }

                if (this.fields[this.date_start]['type'] == 'date')
                {
                    events[e][this.date_start] = openerp.web.auto_str_to_date(events[e][this.date_start]).set({hour: 9}).toString('yyyy-MM-dd HH:mm:ss');
                }
                if (this.date_stop && events[e][this.date_stop] && this.fields[this.date_stop]['type'] == 'date') {
                    events[e][this.date_stop] = openerp.web.auto_str_to_date(events[e][this.date_stop]).set({hour: 17}).toString('yyyy-MM-dd HH:mm:ss');
                }
                calendar_events.push(this.convert_event(events[e]));
            }
            if (!no_filter_reload && this.sidebar && !$.isEmptyObject(this.resource_fields))
            {
                _(this.sidebar.resource_filters).each(function(filter, filter_field)
                {
                    if(self.unit_resource_field == filter_field)
                    {
                        var list = _.map(
                            filter_values[filter_field],
                            function(filter, id)
                            {
                                return {key: id, label: filter.label};
                            });

                        if(list.length == 0)
                        {
                            list = [{key: '', label: scheduler.templates.day_date(scheduler.getState().date)}];
                        }

                        scheduler.createUnitsView({
                            name:"unit",
                            property: self.unit_resource_field,
                            list: list,
                        });
                        scheduler.createTimelineView({
                            name:"timeline",
                            x_unit:"hour",
                            x_date:"%H", 
                            x_step: 2,
                            x_size: 10,
                            x_start: 4,
                            x_length: 8,
                            y_unit: list,
                            y_property: self.unit_resource_field,
                            render: "bar",
                            second_scale: {
                                x_unit: "day",
                                x_date: "%F %d"
                            }
                        });
                    }
                    filter.events_loaded(filter_values[filter_field]);
                });
            }

            this.resource_filter_values = filter_values;
            scheduler.parse(calendar_events, 'json');

            this.refresh_scheduler();
        },
        refresh_scheduler: function()
        {
            this._super.apply(this, arguments);
            this.get_leaves();
        },
        convert_event: function(evt)
        {
            var result = this._super(evt);
            if(this.unit_resource_field && evt[this.unit_resource_field])
            {
                result[this.unit_resource_field] = evt[this.unit_resource_field];
                if(result[this.unit_resource_field] instanceof Array)
                {
                    result[this.unit_resource_field] = result[this.unit_resource_field][0].toString();
                }
            }
            return result;
        },
        get_event_data: function(evt)
        {
            data = this._super.apply(this, arguments);
            if(this.unit_resource_field && evt[this.unit_resource_field])
            {
                data[this.unit_resource_field] = parseInt(evt[this.unit_resource_field]);
            }
            return data;
        },
        get_filters: function()
        {
            var result = _.extend({}, this.resource_fields);
            if(this.color_field && !result[this.color_field])
            {
                result[this.color_field] = this.color_string;
            }
            return result;
        },
        get_leaves: function()
        {
            var self = this;
            openerp.session.rpc('/resource_planning/get_leaves',
                {
                    model: self.dataset.model,
                    date_from: openerp.web.date_to_str(self.range_start),
                    date_to: openerp.web.date_to_str(self.range_stop)
                }).then(
                function(results)
                {
                    _.each(results, function(resources, date)
                    {
                        self.mark_leaves(date, resources)
                    });
                });
        },
        mark_leaves: function(date, resources)
        {
            date = openerp.web.str_to_date(date);
            if(date < this.range_start || date > this.range_stop)
            {
                return;
            }
            scheduler.markTimespan({
                days:  date,
                zones: 'fullday',
                css:   "resource-planning-leave",
                html: this.format_leaves(resources),
            });
        },
        format_leaves: function(resources)
        {
            var result = '<div>';
            _.each(resources, function(resource)
                    {
                        result += "<p>"+_.str.sprintf(
                            _t('%(name)s is on leave'),
                            {name: resource.name}) + '</p>';
                    });
            result += '</div>';
            return result;
        },
        destroy: function()
        {
            scheduler.detachAllEvents();
            this._super.apply(this, arguments);
        }
    });
    openerp.web_calendar.Sidebar.include({
        template: 'CalendarView.sidebar_resource_planning',
        init: function(parent, dataset, view_id, options)
        {
            this.resource_filters={};
            return this._super(parent, dataset, view_id, options);
        },
        start: function()
        {
            var self = this;
            this._super();
            this.mini_calendar.conf.handler = function(date)
                {
                    scheduler.setCurrentView(date, scheduler._mode);
                };
            _(this.getParent().get_filters()).each(function(resource_field_string, resource_field)
                {
                    if(resource_field == self.getParent().color_field && !$.isEmptyObject(self.getParent().resource_fields))
                    {
                        self.filter.destroy();
                    }
                    var $elem = self.$("[data-resource-field='"+resource_field+"']");
                    self.resource_filters[resource_field] = new openerp.resource_planning.SidebarFilter(self, self.getParent(), resource_field);
                    self.resource_filters[resource_field].appendTo($elem);

                });
        },
        get_selections: function()
        {
            var filters={}
            var self=this;
            _(this.resource_filters).each(function(filter)
                    {
                        filters[filter.resource_field]={};
                        filter.$('input:checked').each(function()
                        {
                            filters[filter.resource_field][$(this).val()]=true;
                        });
                    });
            return filters;
        }
    });
    openerp.resource_planning.SidebarFilter = openerp.web_calendar.SidebarFilter.extend({
        init: function(parent, view, resource_field)
        {
            this.resource_field = resource_field;
            return this._super(parent, view);
        },
        events_loaded: function(filters) {
          this.$el.html(openerp.web.qweb.render('CalendarView.sidebar.resource_planning_filter', { filters: filters }));
          if(this.getParent())
          {
              this.getParent().$("[data-resource-field='"+this.resource_field+"']").toggle(this.$('input').length > 1);
          }
            
          this.$el.toggle(this.$('input').length > 1);
        },
        filter_click: function()
        {
            var filters=this.getParent().get_selections();
            scheduler.clearAll();
            if(!$.isEmptyObject(filters))
            {
                this.view.events_loaded(this.view.dataset_events, function(e)
                    {
                        var matches=true;
                        _(filters).each(function(filters, resource_field)
                            {
                                if($.isEmptyObject(filters))
                                {
                                    return;
                                }
                                matches &= filters[e[resource_field][0]];
                            });
                        return matches;
                    }, true);
            }
            else
            {
                this.view.events_loaded(this.view.dataset_events, false, true);
            }
        }
    });
}
