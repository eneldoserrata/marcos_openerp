# -*- coding: utf-8 -*-
import cherrypy
import pprint

import json
import simplejson

def jsonp(func):
    def foo(self, *args, **kwargs):
        callback, _ = None, None
        if 'callback' in kwargs and '_' in kwargs:
            callback, _ = kwargs['callback'], kwargs['_']
            del kwargs['callback'], kwargs['_']
        ret = func(self, *args, **kwargs)
        if callback is not None:
            ret = '%s(%s)' % (callback, simplejson.dumps(ret))
        return ret
    return foo



class server(object):

    @cherrypy.expose
    def default(self, *args, **kwargs):
        pprint.pprint(json.loads(unicode(kwargs.keys()[0], "ISO-8859-1")))

        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(args)
        # pp.pprint(kwargs)
        return "true"

cherrypy.quickstart(server(),"/", )