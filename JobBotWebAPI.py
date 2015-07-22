#BeerBot web control script
#jweob 16/12/14
#Based on the example Script to control a NXT 2-axis CNC "Pancake maker"Written 2/3/11 by Marcus Wanner


#Import nxt library to control the lego
import nxt.locator
from nxt.sensor import *
import nxt, thread, time
from nxt import get_tacho_and_state
from nxt import OutputState
from nxt import motor
#Import colorama
from colorama import init, Fore, Back, Style

class MyBaseMotor(object):
    """Base class for motors"""
    debug = 0
    def _debug_out(self, message):
        if self.debug:
            print message

    def ramped_turn(self, min_power, max_power, tacho_units, ramp_units, step_levels=2):
        ramp_units_per_level = ramp_units / step_levels
        power_units_per_level = (max_power - min_power) / step_levels
        for i in range(0, step_levels, brake=False):
            self.turn(min_power + power_units_per_level * step_levels, ramp_units_per_level)


        remaining_units = tacho_units - ramp_units * 2
        if remaining_units > 0:
            self.turn(max_power, tacho_units - ramp_units * 2, brake=False)

        for i in range(0, step_levels, brake=False):
            self.turn(max_power - power_units_per_level * step_levels, ramp_units_per_level)


    def turn(self, power, tacho_units, brake=True, timeout=1, emulate=True):
        """Use this to turn a motor. The motor will not stop until it turns the
        desired distance. Accuracy is much better over a USB connection than
        with bluetooth...
        power is a value between -127 and 128 (an absolute value greater than
                 64 is recommended)
        tacho_units is the number of degrees to turn the motor. values smaller
                 than 50 are not recommended and may have strange results.
        brake is whether or not to hold the motor after the function exits
                 (either by reaching the distance or throwing an exception).
        timeout is the number of seconds after which a BlockedException is
                 raised if the motor doesn't turn
        emulate is a boolean value. If set to False, the motor is aware of the
                 tacho limit. If True, a run() function equivalent is used.
                 Warning: motors remember their positions and not using emulate
                 may lead to strange behavior, especially with synced motors
        """

        tacho_limit = tacho_units

        if tacho_limit < 0:
            raise ValueError, "tacho_units must be greater than 0!"
        #TODO Calibrate the new values for ip socket latency.
        if self.method == 'bluetooth':
            threshold = 70
        elif self.method == 'usb':
            threshold = 5
        elif self.method == 'ipbluetooth':
            threshold = 80
        elif self.method == 'ipusb':
            threshold = 15
        else:
            threshold = 30 #compromise

        tacho = self.get_tacho()
        state = self._get_new_state()

        # Update modifiers even if they aren't used, might have been changed
        state.power = power
        if not emulate:
            state.tacho_limit = tacho_limit

        self._debug_out('Updating motor information...')
        self._set_state(state)

        direction = 1 if power > 0 else -1
        self._debug_out('tachocount: ' + str(tacho))
        current_time = time.time()
        tacho_target = tacho.get_target(tacho_limit, direction)

        blocked = False
        try:
            while True:
                time.sleep(self._eta(tacho, tacho_target, power) / 2)

                if not blocked: # if still blocked, don't reset the counter
                    last_tacho = tacho
                    last_time = current_time

                tacho = self.get_tacho()
                current_time = time.time()
                blocked = self._is_blocked(tacho, last_tacho, direction)
                if blocked:
                    self._debug_out(('not advancing', last_tacho, tacho))
                    # the motor can be up to 80+ degrees in either direction from target when using bluetooth
                    if current_time - last_time > timeout:
                        if tacho.is_near(tacho_target, threshold):
                            break
                        else:
                            raise motor.BlockedException("Blocked!")
                else:
                    self._debug_out(('advancing', last_tacho, tacho))
                if tacho.is_near(tacho_target, threshold) or tacho.is_greater(tacho_target, direction):
                    break
        finally:
            if brake:
                self.brake()
            else:
                self.idle()

class MyMotor(MyBaseMotor):
    def __init__(self, brick, port):
        self.brick = brick
        self.port = port
        self._read_state()
        self.sync = 0
        self.turn_ratio = 0
        try:
            self.method = brick.sock.type
        except:
            print "Warning: Socket did not report a type!"
            print "Please report this problem to the developers!"
            print "For now, turn() accuracy will not be optimal."
            print "Continuing happily..."
            self.method = None

    def _set_state(self, state):
        self._debug_out('Setting brick output state...')
        list_state = [self.port] + state.to_list()
        self.brick.set_output_state(*list_state)
        self._debug_out(state)
        self._state = state
        self._debug_out('State set.')

    def _read_state(self):
        self._debug_out('Getting brick output state...')
        values = self.brick.get_output_state(self.port)
        self._debug_out('State got.')
        self._state, tacho = get_tacho_and_state(values)
        return self._state, tacho

    #def get_tacho_and_state here would allow tacho manipulation

    def _get_state(self):
        """Returns a copy of the current motor state for manipulation."""
        return OutputState(self._state.to_list())

    def _get_new_state(self):
        state = self._get_state()
        if self.sync:
            state.mode = motor.MODE_MOTOR_ON | motor.MODE_REGULATED
            state.regulation = motor.REGULATION_MOTOR_SYNC
            state.turn_ratio = self.turn_ratio
        else:
            state.mode = motor.MODE_MOTOR_ON | motor.MODE_REGULATED
            state.regulation = motor.REGULATION_MOTOR_SPEED
        state.run_state = motor.RUN_STATE_RUNNING
        state.tacho_limit = motor.LIMIT_RUN_FOREVER
        return state

    def get_tacho(self):
        return self._read_state()[1]

    def reset_position(self, relative):
        """Resets the counters. Relative can be True or False"""
        self.brick.reset_motor_position(self.port, relative)

    def run(self, power=100, regulated=False):
        '''Tells the motor to run continuously. If regulated is True, then the
        synchronization starts working.
        '''
        state = self._get_new_state()
        state.power = power
        if not regulated:
            state.mode = motor.MODE_MOTOR_ON
        self._set_state(state)

    def brake(self):
        """Holds the motor in place"""
        state = self._get_new_state()
        state.power = 0
        state.mode = motor.MODE_MOTOR_ON |motor.MODE_BRAKE |motor.MODE_REGULATED
        self._set_state(state)

    def idle(self):
        '''Tells the motor to stop whatever it's doing. It also desyncs it'''
        state = self._get_new_state()
        state.power = 0
        state.mode =motor.MODE_IDLE
        state.regulation = motor.REGULATION_IDLE
        state.run_state = motor.RUN_STATE_IDLE
        self._set_state(state)

    def weak_turn(self, power, tacho_units):
        """Tries to turn a motor for the specified distance. This function
        returns immediately, and it's not guaranteed that the motor turns that
        distance. This is an interface to use tacho_limit without
        REGULATION_MODE_SPEED
        """
        tacho_limit = tacho_units
        tacho = self.get_tacho()
        state = self._get_new_state()

        # Update modifiers even if they aren't used, might have been changed
        state.mode =motor.MODE_MOTOR_ON
        state.regulation = motor.REGULATION_IDLE
        state.power = power
        state.tacho_limit = tacho_limit

        self._debug_out('Updating motor information...')
        self._set_state(state)

    def _eta(self, current, target, power):
        """Returns time in seconds. Do not trust it too much"""
        tacho = abs(current.tacho_count - target.tacho_count)
        return (float(tacho) / abs(power)) / 5

    def _is_blocked(self, tacho, last_tacho, direction):
        """Returns if any of the engines is blocked"""
        return direction * (last_tacho.tacho_count - tacho.tacho_count) >= 0

brick = True
# Test commit
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
    mx = MyMotor(b, nxt.PORT_A)
    my = MyMotor(b, nxt.PORT_B)
    mz = MyMotor(b, nxt.PORT_C)
    motors = [mx, my, mz]

def turnmotor(m, power, degrees):
    if degrees < 100:
        ramp_degrees = degrees / 2
    else:
        ramp_degrees = 50
    m.ramped_turn(power/10, power, degrees, ramp_degrees)

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


