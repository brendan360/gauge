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
watch_RPM_OBD =0
watch_OIL_OBD =0
watch_BOOST_ADC =0
watch_ITT_OBD = 0
watch_WATER_OBD =0
watch_BLOCK1_ADC =0
watch_BLOCK2_ADC =0
watch_OILP_ADC =0


ADC=0
BT=0
OBD=0


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

topmenu=("Gauges","gaugemenu","ECU","ecumenu","Config","configmenu","Multi 1","QUAD_GAUGE","","backtotop1")
ecumenu=("Clear DTC","ecu_reset","Read DTC","ecu_read","Back","backtotop2")
configmenu=("IP","ipaddress","Reload","reinitialise","Reboot","reboot_pi","Back","backtotop3")

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


#********************
#********************
#####################
#                   #
#Startup code       #
#                   #
##################### 
#********************
#********************

#boot up 
#start obd threads
#start ADC threads
#start display threads
#start monitor and alert thread

disp.Init()

highlightDisplay("test","test")
time.sleep(10)
