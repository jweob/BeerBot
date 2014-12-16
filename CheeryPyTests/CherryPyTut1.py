import cherrypy
#Change port to 8099
cherrypy.engine.stop()
cherrypy.server.httpserver = None
cherrypy.config.update({'server.socket_port': 8099})
cherrypy.engine.start()

class HelloWorld(object):
	@cherrypy.expose
	def index(self):
		return "Hello world!"

if __name__ == '__main__':
	cherrypy.quickstart(HelloWorld())
	
    

