#BeerBot control script
#jweob 19/7/14
#Based on the example Script to control a NXT 2-axis CNC "Pancake maker"Written 2/3/11 by Marcus Wanner

#Import piface module to allow laser and LED control
import pifacedigitalio as pfio

#Import colorama
from colorama import init, Fore, Back, Style
init()

#Import nxt library to control the lego
import nxt.locator
from nxt.sensor import *
import nxt, thread, time
b = nxt.find_one_brick()

#Initialise piface
pfio.init()


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
    [0, 0, 80, 20.779],
    [0, 1, 80, 20.779],

#Left 1
    [1, 0, 80, 3.4696],
    [1, 1, -80, 3.4696],


#Right 2
    [2, 0, -80, 3.4696],
    [2, 1, 80, 3.4696],

#Claw close 3
    [3, 2, -80, 50],


#Claw open 4
    [4, 2, 80, 50],

#Back
    [5, 0, -80, 20.779],
    [5, 1, -80, 20.799],

#Keep seconds = 99 as no command
                
)
#how long from start until the last instruction is ended
length = 10

def runinstruction(i, Value):
    motorid, speed, degrees = i
    #THIS IS THE IMPORTANT PART!
    thread.start_new_thread(
        turnmotor,
        (motors[motorid], speed, degrees*Value))

#main loop
seconds = 0
ClawPos = 0
laser = 0 #0 means laser is off
laser_status = [Fore.BLACK + "Off", Fore.YELLOW + "On (EXTREME DANGER)"]
headlights = 0 #0 is off, 1 is white, 2 is disco
headlights_status = ["Off", Fore.WHITE + "On (white)", Fore.YELLOW + "Disco Mode"]
print (Back.BLUE + Style.BRIGHT)
print ("WELCOME TO BEERBOT")
print ("jweob 23/7/2014")
print (Back.RESET)
while 1:
# Get the instruction:
    Command = raw_input(Fore.WHITE + Style.BRIGHT + "Commands are: wasd to move, r and f for claw, t to toggle LASER, h to cycle headlights, q for quit\nFor wasd you can append a number for cm moved (w & s) or degrees rotated (a & d)\nIf you just enter the letter on its own default move is 10cm or 10 degrees\nCommand+Enter>"  + Fore.RESET + Style.RESET_ALL)
    
    if Command == "":
        CommandStart = Command
    else:
        CommandStart = Command[0]

    if ((len(Command) > 1) and is_number(Command[1:])):
        print ("Custom Command Accepted")
        CommandValue = int(Command[1:])
    else:
        CommandValue = 0
                
    if CommandStart == "w":
        print ("Forward!")
        seconds = 0
        if CommandValue == 0:
            CommandValue = 10
            
    elif CommandStart == "s":
        print ("Retreat!")
        seconds = 5        
        if CommandValue == 0:
            CommandValue = 10
                          
    elif CommandStart == "a":
        print ("Left!")
        seconds = 1
        if CommandValue == 0:
            CommandValue = 10
                                      
    elif CommandStart ==  "d":               
        print ("Right!")
        seconds = 2
        if CommandValue == 0:
            CommandValue = 10
                
    elif CommandStart == "r":
        if ClawPos == 3:
            print("Claw already closed all the way!")
        else:
            ClawPos = ClawPos + 1
            print ("Claw!")
            seconds = 3
            if CommandValue == 0:
                CommandValue = 1
                
    elif CommandStart == "f":
        ClawPos = ClawPos - 1
        print ("Unclaw!")
        seconds = 4
        if CommandValue == 0:
            CommandValue = 1

    elif CommandStart == "t":
        seconds = 99
        if CommandValue == 0:
            CommandValue = 1
        if laser == 0:
            print ("LASER ON!")
            pfio.digital_write(0,1)
            laser = 1
        elif laser ==1:
            print ("LASER OFF (awwww...!)")
            pfio.digital_write(0,0)
            laser =0

    elif CommandStart == "h":
        seconds = 99
        if CommandValue == 0:
            CommandValue = 1
        pfio.digital_write(1,1)
        time.sleep(1)
        pfio.digital_write(1,0)
            
        if headlights == 0:
            print ("Headlights on (white)")
            headlights = 1
        elif headlights == 1:
            print ("Headlights on (disco)")
            headlights = 2
        elif headlights == 2:
            print ("Headlights off")
            headlights = 0    
                
    elif (CommandStart == ""  or CommandStart == "\n"):
	print ("Nothing entered")

                
    elif CommandStart == "q":
        print ("Goodbye!" + Fore.RESET + Back.RESET + Style.RESET_ALL)
        colorama.deinit()
        break

    print( "---Status Report Begins---")
    print (Back.BLUE + Style.BRIGHT + Fore.WHITE + "Beerfinder range:"), Ultrasonic(b, PORT_2).get_sample(), ("cm"), (Back.RED + " Laser status: "), laser_status[laser],( Back.MAGENTA + Fore.BLACK + " Headlights status: "), headlights_status[headlights], Fore.RESET + Back.RESET +Style.RESET_ALL, (" ")
    print("---Status Report Ends---" + Fore.RESET + Back.RESET)
                
#Print "Tick %d" % seconds
    for i in instructions:
        if i[0] == seconds:
            runinstruction(i[1:], CommandValue)
    #time.sleep(1)
