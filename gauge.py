#********************
#********************
#####################
#                   #
#IMPORTS            #
#                   #
##################### 
#********************
#********************
import board
import digitalio
import socket
import time
import _thread
import threading
import busio
from digitalio import DigitalInOut, Direction, Pull
from PIL import Image, ImageDraw, ImageFont
import fcntl
import struct
import os
import bluetooth
import obd
from obd import OBDStatus
import sys
import spidev as SPI
from RPi import GPIO
sys.path.append("..")
from lib import LCD_1inch28
import colorsys
import signal
import sys
import ioexpander as io






#********************
#********************
#####################
#                   #
#GLOBAL CONFIGS     #
#                   #
##################### 
#********************
#********************

address="/home/pi/gauge/"

###
#gauge value setup
###

#Global variables


ADC=0
BT=0
OBD=0
bootState={"bth":[0,"fail"],
           "adc":[0,"fail"],
           "obd":[0,"fail"]
           }


#Monitor limits
up_RPM_OBD =0
up_OIL_OBD =0
up_BOOST_ADC =0
up_ITT_OBD = 0
up_WATER_OBD =0
up_BLOCK1_ADC =0
up_BLOCK2_ADC =0
up_OILP_ADC =0
#--------------------------#


###
#DISPLAY SETUP
###
#PIN CONFIG LCD
RST=27
DC=25
BL=18
bus=0
device = 0

#Display
SW=26
disp = LCD_1inch28.LCD_1inch28()
rotation=0
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setmode(GPIO.BCM)
#--------------------------#



###
#Rotary encoder
###
SW = 26
SW1=21
rotaryCounter=0
oldEncValue=0
newEncValue=0
movementValue=0
I2C_ADDR = 0x0F  # 0x18 for IO Expander, 0x0F for the encoder breakout
POT_ENC_A = 12
POT_ENC_B = 3
POT_ENC_C = 11

PIN_RED = 1
PIN_GREEN = 7
PIN_BLUE = 2
BRIGHTNESS = 0.30                # Effectively the maximum fraction of the period that the LED will be on
PERIOD = int(255 / BRIGHTNESS)  # Add a period large enough to get 0-255 steps at the desired brightness
ioe = io.IOE(i2c_addr=I2C_ADDR, interrupt_pin=4)

# Swap the interrupt pin for the Rotary Encoder breakout
if I2C_ADDR == 0x0F:
    ioe.enable_interrupt_out(pin_swap=True)

ioe.setup_rotary_encoder(1, POT_ENC_A, POT_ENC_B, pin_c=POT_ENC_C)
ioe.set_pwm_period(PERIOD)
ioe.set_pwm_control(divider=2)  # PWM as fast as we can to avoid LED flicker
ioe.set_mode(PIN_RED, io.PWM, invert=True)
ioe.set_mode(PIN_GREEN, io.PWM, invert=True)
ioe.set_mode(PIN_BLUE, io.PWM, invert=True)
r, g, b, = 0, 0, 0


###
#Display helper setup
###

#fonts
font = ImageFont.truetype(address+"arial.tff", 42)
font2 = ImageFont.truetype(address+"arial.tff", 20)
font3 = ImageFont.truetype(address+"arial.tff", 12)
gfont = ImageFont.truetype(address+"arial.tff", 54)
#--------------------------#



###
#OBD setup
###

#BT info
btmac="00:04:3E:4A:26:B0"
btname="OBDLink LX"


###
#menu setup
###

topmenu=["Gauges","gaugemenu","ECU","ecumenu","Config","configmenu","Multi 1","QUAD_GAUGE","","backtotop1"]
ecumenu=["Clear DTC","ecu_reset","Read DTC","ecu_read","Back","backtotop2"]
configmenu=["IP","ipaddress","Reload","reinitialise","Reboot","reboot_pi","Back","backtotop3"]
gaugemenu=["Back","backttop2"]
#              obd name    PID, location, enabled or false##, Friendly Name,value,pid squence, pid array
gaugeItems={"FUEL_STATUS":["03","OBD",0,"Fuel Status","",2,"a"],
            "ENGINE_LOAD":["04","OBD",0,"Engine Load","",3,"a"],
            "COOLANT_TEMP":["05","OBD",0,"Water C","",4,"a"],
            "FUEL_PRESSURE":["0A","OBD",0,"Fuel Pres","",9,"a"],
            "INTAKE_PRESSURE":["0B","OBD",0,"Intake Pres","",10,"a"],
            "RPM":["0C","OBD",0,"RPM","",11,"a"],
            "SPEED":["0D","OBD",0,"Speed","",12,"a"],
            "TIMING_ADVANCE":["0E","OBD",0,"Timing","",13,"a"],
            "INTAKE_TEMP":["0F","OBD",0,"Intake C","",14,"a"],
            "MAF":["10","OBD",0,"MAF","",15,"a"],
            "THROTTLE_POS":["11","OBD",0,"Throttle","",15,"a"],
            "RUN_TIME":["1F","OBD",0,"Run Time","",30,"a"],
            "FUEL_LEVEL":["2F","OBD",0,"Fuel %","",14,"b"],
            "BAROMETRIC_PRESSURE":["33","OBD",0,"Out Pres","",18,"b"],
            "AMBIANT_AIR_TEMP":["46","OBD",0,"Air Temp","",5,"c"],
            "FUEL_TYPE":["51","OBD",0,"Fuel Type","",16,"c"],
            "FUEL_RATE":["5E","OBD",0,"Fuel Rate","",29,"c"],
            "OIL_TEMP":["5C","OBD",0,"Oil C","",27,"c"],
            "OIL_PRESSURE_ADC":["ADCPIN0","ADC",1,"Oil Pres","",0,"adc"],
            "BOOST_ADC":["ADCPIN1","ADC",1,"Boost","",1,"adc"],
            "BLOCK_TEMP1_ADC":["ADCPIN2","ADC",1,"Block1 C","",2,"adc"],
            "BLOCK_TEMP2_ADC":["ADCPIN3","ADC",1,"Block2 C","",3,"adc"],
            "CABIN_TEMP_i2c":["TEMPADDR","I2C",0,"Cabin C","",4,"adc"]
            }




#********************
#********************
#####################
#                   #
#Connection OBD/ADC #
#   Threads         #
##################### 
#********************
#********************

#start OBD connection wait for connection if non received mark as no obd and  change menu

#start ADC thread and start saving global variables. if no data received mark as no ADC and change menu

#obd check for valid pids and update gauge status if avaliable



#********************
#********************
#####################
#                   #
#ALERT      OBD/ADC #
#   Threads         #
##################### 
#********************
#********************

#monitor global configs for reader values and if go over set limit alert via buzzer and swap screen to that monitor




#********************
#********************
#####################
#                   #
#Display/menu       #
#   Threads         #
##################### 
#********************
#********************

#menu serup goes here and display of gauge screens
def menuDisplay(currentMenu,menu):
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    
    if (currentMenu-1 <0):
        minusMenu=(len(menu)-2)
    else:
        minusMenu=currentMenu-2
    
    if (currentMenu+2 >= len(menu)):
        plusMenu=0
    else:
        plusMenu=currentMenu+2

    if (currentMenu+4 == len(menu)):
        plus2Menu=0
        
    elif (currentMenu+4 == (len(menu)+2)):
        plus2Menu=2
    else:
        plus2Menu=currentMenu+4

    if (currentMenu-4 == -1):
        minus2Menu=(len(menu)-2)
    elif (currentMenu-4 == -2):
        minus2Menu=(len(menu)-2)
    else:
        minus2Menu = currentMenu-4
    if (len(menu)/2)>= 5:
        draw.text((35,40), menu[minus2Menu], font=font3, fill="WHITE")
        draw.text((35,190), menu[plus2Menu],font = font3, fill="WHITE")
    
    draw.text((55, 65), menu[minusMenu], font=font2, fill="WHITE")
    draw.text((10, 95),">"+menu[currentMenu], font=font, fill=255)
    draw.text((55, 155), menu[plusMenu], font=font2, fill="WHITE")
    
    
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)


def menuloop(item,menu):
    def buttonPushed(item,menu):
        doaction(item,menu)
    global newEncValue
    global oldEncValue
    while True:
        if ioe.get_interrupt():
            newEncValue=ioe.read_rotary_encoder(1)
            ioe.clear_interrupt()

            if newEncValue>oldEncValue:
                item-=2
                oldEncValue=newEncValue
            if newEncValue<oldEncValue:
                item+=2
                oldEncValue=newEncValue
            
        if item == (len(menu)):
            item=0
        if item <0:
            item=(len(menu))-2
        
        menuDisplay(item,menu)
        
        buttonState=GPIO.input(SW)
        if buttonState == False:
            doaction(item,menu)

def doaction(item,menu):
    time.sleep(.333)
    if (menu[item]=="Gauges"):
        menuloop(0,gaugemenu)
    if (menu[item]=="ECU"):
        menuloop(0,ecumenu)
    if (menu[item] == "Config"):
        menuloop(0,configmenu)
    highlightDisplay("Loading",menu[item])
    print(menu[item+1])
    eval(menu[item+1] + "()")
    
def backtotop1():
    menuloop(0,topmenu)
def backtotop2():
    menuloop(2,topmenu)
def backtotop3():
    menuloop(4,topmenu)

    
def clearDisplay():
    disp.clear()

def setupDisplay():
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)
    return image,draw

def highlightDisplay(TEXT,hightext):
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    ##(accross screen),(upand down))(100,100 is centre)
    draw.text((70,30),hightext, fill = "WHITE", font=font2)
    draw.text((15,95),TEXT, fill = "WHITE", font =font)
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)

def highlightbootDisplay(boot):
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]



   if boot=="bth": 
        draw.text((40,40),"BTH", fill = "WHITE", font=font)
        draw.text((150,40),".....", fill = "WHITE", font=font)
        draw.text((40,93),"ADC", fill = "WHITE", font =font)
        draw.text((150,93),".....", fill = "WHITE", font=font)
        draw.text((40,145),"OBD", fill = "WHITE", font=font)
        draw.text((150,145),".....", fill = "WHITE", font=font)
    

    if boot=="bth":
        if state=="fail":
            faildot="."*bootstate['bth'](0)
            draw.text((40,40),"BTH", fill = "WHITE", font=font)
            draw.text((150,40),".....", fill = "WHITE", font=font)
            draw.text((150,40),faildot, fill = "RED", font=font)
            im_r=image.rotate(rotation)
            disp.ShowImage(im_r)
            if count==5:
                draw.text((40,40),"BTH", fill = "RED", font=font)
                im_r=image.rotate(rotation)
                disp.ShowImage(im_r)
#        else:
#            faildot="."*count
#            draw.text((40,40),"BTH", fill = "GREEN", font=font)
#            draw.text((150,40),faildot, fill = "GREEN", font=font)
#           im_r=image.rotate(rotation)
#            disp.ShowImage(im_r)



    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)

#********************
#********************
#####################
#                   #
#config items       #
#                   #
##################### 
#********************
#********************

#non gauge items go here such as reset reboot ip address
#DTC read and reset also setup in here
def reboot_pi():
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    draw.text((30,85),"REBOOT", font=font, fill=255)
    draw.text((20,150),"Press button to cancel",font=font2, fill="WHITE")
    tempcount=0
    draw.text((60,30),"..........", font=font, fill="WHITE")
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    time.sleep(5) 
    
    while tempcount <=10:
        buttonState=GPIO.input(SW)
        if buttonState == False:
            menuloop(4,topmenu)
        diedots="."*tempcount
        draw.text((60,30),diedots, font=font, fill=255)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        time.sleep(1)
        tempcount+=1

    os.system('sudo reboot')

def reinitialise():
    resetComm()
    firstBoot()

def resetComm():
    os.system('sudo rfcomm release all')
    time.sleep(5)
    os.system('sudo rfcomm bind rfcomm0 00:04:3E:4A:26:B0')
    
def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def ipaddress():
    IP=getIpAddress()
    highlightDisplay(IP,"Car Guage")
    time.sleep(5)
    menuloop(0,configmenu)


#********************
#********************
#####################
#                   #
#Startup code       #
#                   #
##################### 
#********************
#********************
def firstBoot():
    disp.Init()
    image=Image.open(address+'logo.jpg')
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    time.sleep(1)
    os.system('sudo rfcomm bind rfcomm0 '+btmac)
    connectBT()

def connectBT():
    global BT
    print("connecting BT")
    i=0
    while i<5:
        print("looping",i)
        BTconnected=os.system('hcitool name "'+btname+'"')
        if btname in str(BTconnected):
            print("BT conected")
            BT=1
            bootState['bth']=(1,"win")
            highlightbootDisplay("bth")
            return
        i=i+1
        time.sleep(2)
        bootState['bth']=(i,"fail")
        highlightbootDisplay("bth")
    print("BT not avaliable")
    BT=0

def connectADC():
    print("connecting ADC")


def connectOBD():
    print("connecting obd")


#boot up 
#start obd threads
#start ADC threads
#start display threads
#start monitor and alert thread

def cleanupMenu():
    inactiveItems=[]
    for key, value in gaugeItems.items():
        if value[2] == 0:
            inactiveItems.append(key)
    
    for x in inactiveItems:
        del gaugeItems[x]
    
    for key,value in gaugeItems.items():
        gaugemenu.insert(0,value[3])
        gaugemenu.insert(1,key)



firstBoot()
highlightbootDisplay("adc")
time.sleep(10)
#cleanupMenu()

print("starting thread1")
#try:
#    threading.Thread(target=menuloop, args=(0,topmenu)).start()
#except:
#    print("failed threads")


