import cherrypy
#sets cherrypy to 8099 port
cherrypy.engine.stop()
cherrypy.server.httpserver = None
cherrypy.config.update({'server.socket_port': 8099})
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.engine.start()

import random
import string

import cherrypy

class StringGenerator(object):
	@cherrypy.expose
	def index(self):
		return "Hello world!"

	@cherrypy.expose
	def generate(self):
		return ''.join(random.sample(string.hexdigits,8))

if __name__ == '__main__':
	cherrypy.quickstart(StringGenerator())


