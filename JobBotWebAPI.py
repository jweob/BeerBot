#BeerBot web control script
#jweob 16/12/14
#Based on the example Script to control a NXT 2-axis CNC "Pancake maker"Written 2/3/11 by Marcus Wanner


#Import nxt library to control the lego
import nxt.locator
from nxt.sensor import *
import nxt, thread, time
#Import colorama
from colorama import init, Fore, Back, Style

brick = True

try:
    b = nxt.find_one_brick()
except:
    print "Brick not connected"
    brick = False

try:
    #Initialise piface
    pfio.init()
    init()
except:
    print "PiFace not connected"

#import cherrypy for web stuff
import cherrypy
#sets cherrypy to 8099 port and allows access from other computers
cherrypy.engine.stop()
cherrypy.server.httpserver = None
cherrypy.config.update({'server.socket_port': 8099})
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.engine.start()

#needed for importing static content
import os, os.path


#Set up directory for html files
MEDIA_DIR = os.path.join(os.path.abspath("."), "Media")

if brick:
    mx = nxt.Motor(b, nxt.PORT_A)
    my = nxt.Motor(b, nxt.PORT_B)
    mz = nxt.Motor(b, nxt.PORT_C)
    motors = [mx, my, mz]

def turnmotor(m, power, degrees):
    m.turn(power, degrees)

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False 

#here are the instructions...
#the first value is the time to start the instruction
#the second is the axis (0 for x, 1 for y)
#the third is the power
#the fourth is the degrees
#it's probably not a good idea to run simultaneous turn
#functions on a single motor, so be careful with this
instructions = (

#Forward 0
    ['FWD', 0, 80, 20.779],
    ['FWD', 1, 80, 20.779],

#Left 1
    ['LFT', 0, 80, 3.4696],
    ['LFT', 1, -80, 3.4696],


#Right 2
    ['RGT', 0, -80, 3.4696],
    ['RGT', 1, 80, 3.4696],

#Claw close 3
    ['CLS', 2, -80, 50],


#Claw open 4
    ['OPN', 2, 80, 50],

#Back
    ['BCK', 0, -80, 20.779],
    ['BCK', 1, -80, 20.799],

#Keep seconds = 99 as no command
                
)
#how long from start until the last instruction is ended
length = 10

def runinstruction(i, Value):
    if brick:
        motorid, speed, degrees = i
        thread.start_new_thread(
            turnmotor,
            (motors[motorid], speed, degrees*Value))
    else:
        print "Instruction received but no brick: " + str(i) + " " + str(Value)

def RunLegoCommand(CMD, CommandValue):
    for i in instructions:
        if i[0] == CMD:
            runinstruction(i[1:], CommandValue)

class WebBot(object):
	@cherrypy.expose
	def index(self):
		return file('index.html')

class WebBotGenerator(object):
	exposed = True

	@cherrypy.tools.accept(media='text/plain')
	def POST(self, CMD='', CommandValue=10):
		if CMD == 'OPN' or CMD == 'CLS':
			CommandValue = 1
		if CMD == 'LS+':
			pfio.digital_write(0,1)
		elif CMD == 'LS-':
			pfio.digital_write(0,0)
		elif CMD == 'HLT':
			pfio.digital_write(1,1)
			time.sleep(1)
			pfio.digital_write(1,0)
		else:
			RunLegoCommand(CMD, int(CommandValue))
		response = 'Command received: ' + CMD + str(CommandValue)
		return response


if __name__ == '__main__':
        conf = {
				'/': {
					'tools.sessions.on': True,
					'tools.staticdir.root':os.path.abspath(os.getcwd())
				},
				'/static': {
					'tools.staticdir.on': True,
					'tools.staticdir.dir': './public'
				},
				'/generator':{
					'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
					'tools.response_headers.on': True,
					'tools.response_headers.headers': [('Content-Type', 'text/plain')]
				}
			}
webapp = WebBot()
webapp.generator = WebBotGenerator()
cherrypy.quickstart(webapp, '/', conf)


