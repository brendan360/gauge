#!/usr/bin/python3

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
disp = LCD_1inch28.LCD_1inch28()
rotation=0
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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



