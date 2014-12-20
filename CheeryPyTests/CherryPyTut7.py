#needed for importing static content
import os, os.path


import cherrypy
#sets cherrypy to 8099 port and allows access from other computers
cherrypy.engine.stop()
cherrypy.server.httpserver = None
cherrypy.config.update({'server.socket_port': 8099})
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.engine.start()

import random
import string

class StringGeneratorWebService(object):
	exposed = True

	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		return cherrypy.session['mystring']

	def POST(self, length=8):
		some_string = ''.join(random.sample(string.hexdigits, int(length)))
		cherrypy.session['mystring'] =some_string
		return some_string

	def PUT(self, another_string):
		cherrypy.session['mystring'] = another_string

	def DELETE(self):
		cherrypy.session.pop('mystring',None)

if __name__ == '__main__':
	conf = {
			'/': {
				'request.dispatch':cherrypy.dispatch.MethodDispatcher(),
				'tools.sessions.on': True,
				'tools.response_headers.on': True,
				'tools.response_headers.headers': [('Content-Type', 'text/plain')],
				}
			}
	cherrypy.quickstart(StringGeneratorWebService(), '/', conf)
	
