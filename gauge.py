#!/usr/bin/python3
  
### if obd becomes unbresponice use screen /dev/rfcomm0 and run these commands ATL1, ATH1, ATS1, ATAL  

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
import socket
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import fcntl
import struct
import os
import git 
import obd
from obd import OBDStatus
import sys
import spidev as SPI
sys.path.append("..")
from lib import LCD_1inch28
import colorsys
import signal
import sys
import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
from adafruit_seesaw import seesaw, neopixel, rotaryio, digitalio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_htu31d
from adafruit_bme280 import basic as adafruit_bme280
i2c = board.I2C() 
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)





try:
    import _pixelbuf
except ImportError:
    import adafruit_pypixelbuf as _pixelbuf



#********************
#********************
#####################
#                   #
#GLOBAL CONFIGS     #
#                   #
##################### 
#********************
#********************
 

###
#gauge value setup
###

#Global variables

obdConnection="/dev/ttyS0"

bme280.sea_level_pressure = 1014.5

breadCrumb=[0,"topmenu"]
ingauge =0
rpmHIGH=0

bootState={"adc":[0,"fail",0],
           "elm":[0,"fail",0],
           "obd":[0,"fail",0]
           }
address="/home/pi/gauge/"
alertScreen=0
ads=''
statusState = ""

fafbAlert="SPEED"
fafbTrigger=105

repo = git.cmd.Git(address)


###
#DISPLAY SETUP
###

#PIN CONFIG LCD
RST=27
DC=25
BL=18
bus=0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation=180
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
#Encoder setup
###
seesaw = seesaw.Seesaw(board.I2C(), addr=0x36)
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
#--------------------------#

###
#buzzer setup
####
BuzzerPin = 21
FanPin = 25
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BuzzerPin,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(FanPin,GPIO.OUT, initial=GPIO.LOW)
buzzerMute=0


###
#menu setup
###

topmenu=["Gauges","gaugemenu","ECU","ecumenu","Config","configmenu","Multi 1","QUAD_GAUGE","Temp Multi","TEMP_GAUGE"]
ecumenu=["Clear DTC","ecu_reset","Read DTC","ecu_read","Back","backtotop2"]
configmenu=["Mute", "muteBuzzer", "IP","ipaddress","Update","update","Reload","reinitialise","Reboot","reboot_pi","Back","backtotop3"]
gaugemenu=["Back","backtotop2"]
#              obd name    PID, location, enabled or false##, Friendly Name,value,pid squence, pid array,alertlow,alerthigh,alertcount
gaugeItems={"ENGINE_LOAD":["04","OBD",0,"Engine Load","0",3,"a","na","100",0],
 #           "COOLANT_TEMP":["05","OBD",0,"Water °C","0",4,"a","na","100",0],
 #           "FUEL_PRESSURE":["0A","OBD",0,"Fuel Pres","0",9,"a","na","100",0],
            "INTAKE_PRESSURE":["0B","OBD",0,"Intake Pres","0",10,"a","na","100",0],
            "RPM":["0C","OBD",0,"RPM","0",11,"a","na","6000",0],
            "SPEED":["0D","OBD",0,"Speed","0",12,"a","na","na",0],
            "TIMING_ADVANCE":["0E","OBD",0,"Timing","0",13,"a","na","100",0],
            "INTAKE_TEMP":["0F","OBD",0,"Intake C","0",14,"a","na","100",0],
            "MAF":["10","OBD",0,"MAF","0",15,"a","na","100",0],
            "THROTTLE_POS":["11","OBD",0,"Throttle","0",15,"a","na","na",0],
            "RUN_TIME":["1F","OBD",0,"Run Time","0",30,"a","na","na",0],
            "FUEL_LEVEL":["2F","OBD",0,"Fuel %","0",14,"b","na","na",0],
            "BAROMETRIC_PRESSURE":["33","OBD",0,"Air Pres","0",18,"b","na","na",0],
            "AMBIANT_AIR_TEMP":["46","OBD",0,"Air °C","0",5,"c","na","na",0],
 #           "FUEL_RATE":["5E","OBD",0,"Fuel Rate","0",29,"c","na","100",0],
            "OIL_TEMP":["5C","OBD",0,"Oil C","0",27,"c","na","100",0],
            "OIL_PRESSURE_ADC":["ADCPIN0","ADC",0,"Oil Pres","0",0,"adc","na","100",0],
            "BOOST_ADC":["ADCPIN1","ADC",0,"Boost","0",0,"adc","na","20",0],
            "BLOCK_TEMP1_ADC":["ADCPIN2","ADC",0,"Block °C","0",2,"adc","na","90",0],
            "BLOCK_TEMP2_ADC":["ADCPIN3","ADC",0,"Head °C","0",3,"adc","na","90",0],
            "CABIN_TEMP_i2c":["TEMPADDR","I2C",1,"Cabin °C","0",4,"adc","na","na",0],
            "ALTITUDE_i2c":["ALTADDR","I2C",1,"Altitude","0",4,"adc","na","na",0],
            "CPU_temp":["ALTADDR","I2C",1,"CPU °C","0",4,"adc","na","60",0]
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

def connectADC():
    global ads
    print("Connecting ADC")
    i=0
    while i<5:
        try:
            ads = ADS.ADS1115(i2c)
            print("     ADC connected")
            bootState['adc']=(i,"win",1)
            highlightbootDisplay()
            return
        except:
            i+=1
            bootState['adc']=(i,"fail",0)
            highlightbootDisplay()
            time.sleep(1)
    bootState['adc']=(i,"fail",0)
    print("     ADC failed")

def connectELM():
    print("Connecting ELM")
    i=0
    global statusState
    while i<5:
        try:
            connection = obd.OBD(obdConnection, check_voltage=False, baudrate=9600)
            statusState=connection.status()
            if statusState == "ELM Connected":
                print("     ELM conected")
                bootState['elm']=(i,"win",1)
                highlightbootDisplay()
                connection.close()
                return
            elif statusState == "Car Connected":
                bootState['elm']=(i,"win",1)
                bootState['obd']=(0,"win",1)
                highlightbootDisplay()
                connection.close()
                return
            
            else:
                i=i+1
                bootState['elm']=(i,"fail",0)
                highlightbootDisplay()
                continue
        except:
            i=i+1
            bootState['elm']=(i,"fail",0)
            highlightbootDisplay()

def connectOBD():
    global statusState
    print("Connecting OBD")
    i=0
    if bootState['elm'][1]=="fail":
       bootState['obd']=(5,"fail",0) 
       return
    
    if statusState == "Car Connected": 
        return
        
    else:
        statusState=""
        while i<5:
            try:
                connection = obd.OBD(obdConnection, check_voltage=False, baudrate=9600)
                statusState=connection.status()
                if statusState == "Car Connected":
                    print("     OBD conected")
                    bootState['obd']=(i,"win",1)
                    highlightbootDisplay()
                    connection.close()
                    return
                else:
                    i=i+1
                    time.sleep(1)
                    bootState['obd']=(i,"fail",0)
                    highlightbootDisplay()
                    continue
            except:
                i=i+1
                bootState['obd']=(i,"fail",0)
                highlightbootDisplay()



#********************
#********************
#####################
#                   #
#running OBD/ADC    #
#   Threads         #
##################### 
#********************
#********************

def obdTHREAD():
    connection = obd.OBD(obdConnection, check_voltage=False, baudrate=9600)
    while True:
        for i in gaugeItems.keys():
            if gaugeItems[i][1]=="OBD":
                cmd= "gaugeItems[i][4]=connection.query(obd.commands."+str(i)+")"
                exec(cmd)
                if gaugeItems[i][4].value == None:
                    print("****")
                    print(gaugeItems[i][3])
                    print("none")
                else:
                    gaugeItems[i][4]=str(round(gaugeItems[i][4].value.magnitude))
    connection.close()

def adcTHREAD():
    old_min=1088
    old_max=32767
    new_min=0
    new_max=150
    
    bold_min=0
    bold_max=32767
    bnew_min=0
    bnew_max=34
    
    while True:
        temperature=bme280.temperature
        relative_humidity = bme280.relative_humidity
        altitude= bme280.altitude
        gaugeItems["CABIN_TEMP_i2c"][4]=round(temperature)
        gaugeItems["ALTITUDE_i2c"][4]=round(altitude)
        chan1 = AnalogIn(ads, ADS.P2)  #oil pres
        chan2 = AnalogIn(ads, ADS.P3)  #booost
        chan3 = AnalogIn(ads, ADS.P0)  #block 1
        chan4 = AnalogIn(ads, ADS.P1)  #block 2

        adcoil=chan3.value
        adcboost=chan4.value

        oilpsi=((adcoil - old_min)/(old_max-old_min))*(new_max-new_min)+new_min
        oilpsi=round(oilpsi)
        
        boostpsi=((adcboost - bold_min)/(bold_max-bold_min))*(bnew_max-bnew_min)+bnew_min
        boostpsi=round((boostpsi - (gaugeItems["ALTITUDE_i2c"][4] * 0.0145038)),1)
        time.sleep(.2)
        thermistor1 = chan1
        R1 = 10000/ (40634/thermistor1.value - 1)
        thermistor2 = chan2
        R2 = 10000 / (40634/thermistor2.value - 1)
        gaugeItems["BLOCK_TEMP1_ADC"][4]=round(steinhart_temperature_C(R1))
        gaugeItems["BLOCK_TEMP2_ADC"][4]=round(steinhart_temperature_C(R2))
        gaugeItems["OIL_PRESSURE_ADC"][4]=oilpsi 
        gaugeItems["BOOST_ADC"][4]=boostpsi 
        cpu = CPUTemperature()
        gaugeItems["CPU_temp"][4]=cpu.temperature



#********************
#********************
#####################
#                   #
#ALERT      OBD/ADC #
#   Threads         #
##################### 
#********************
#********************

def flashLed():
    global buzzerMute
    pixel = neopixel.NeoPixel(seesaw, 6, 1)
    pixel.brightness = 0.5
    i=0
    if buzzerMute == 0:    
        while i <=5:
            color = 0  # start at red
            pixel.brightness = 0.9
            GPIO.output(BuzzerPin,GPIO.HIGH)
            pixel.fill(_pixelbuf.colorwheel(color))
            time.sleep(.5)
            pixel.brightness = 0.0
            GPIO.output(BuzzerPin,GPIO.LOW)
            pixel.fill(_pixelbuf.colorwheel(color))
            time.sleep(.5)
            i+=1
    else:
        while i <=5:
            color = 0  # start at red
            pixel.brightness = 0.9
            pixel.fill(_pixelbuf.colorwheel(color))
            time.sleep(.5)
            pixel.brightness = 0.0
            pixel.fill(_pixelbuf.colorwheel(color))
            time.sleep(.5)
            i+=1

def shiftALERTING():
    pixel = neopixel.NeoPixel(seesaw, 6, 1)
    pixel.brightness = 0.5
    i=1
    while i <=2:
        color = 128  # start at red
        pixel.brightness = 0.9
        pixel.fill(_pixelbuf.colorwheel(color))
        time.sleep(.1)
        pixel.brightness = 0.0
        pixel.fill(_pixelbuf.colorwheel(color))
        time.sleep(.1)
        i+=1

def fafbALERTING():
    global alertScreen
    global ingauge
    global breadCrumb
    fafb=1
    while fafb <=5:
        image=Image.open(address+'fafb.jpg')
        time.sleep(.5)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        image=Image.open(address+'fafb2.jpg')
        time.sleep(.5)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        fafb+=1
    alertScreen =0
    if ingauge == 0:  
        menuloop(breadCrumb[0],breadCrumb[1])
    if ingauge == 1:
        doaction(breadCrumb[0],breadCrumb[1])  

def highALERTING(discard,key):
    global alertScreen
    global ingauge
    global breadCrumb
    alert=1
    while alert <=8:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((53,95),str(gaugeItems[key][4]),font=gfont, fill="RED")
        draw.text((50,26),str(gaugeItems[key][3]), font=font, fill="RED") 
        time.sleep(.5)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        alert+=1
    alertScreen =0
    if ingauge == 0:  
        menuloop(breadCrumb[0],breadCrumb[1])
    if ingauge == 1:
        doaction(breadCrumb[0],breadCrumb[1])   
        
def alertTHREAD():
    time.sleep(5)
    global alertScreen
    print("starting alert thread")
    while True:

        for key,value in gaugeItems.items():
            if value[9] > 0:
                value[9]-=1
                
            if key == fafbAlert:
                if round(int(value[4]))== fafbTrigger:
                    if value[9] == 0:
                        value[9]=1100000
                        time.sleep(2)
                        alertScreen=1
                        print("FAFB")
                        threading.Thread(target=fafbALERTING).start()
                  
            if key == "RPM":
                if round(int(value[4])) >= 5500 and round(int(value[4])) < 6500:
                    if value[9] == 0:
                        value[9]=105500
                        threading.Thread(target=shiftALERTING).start()

            if value[8]=="na":
                continue
                
            if key == "CPU_temp":
                if int(value[4]) >= int(value[8]):
                    GPIO.output(FanPin,GPIO.HIGH)
                else:
                    GPIO.output(FanPin,GPIO.LOW)
                

            
            elif int(value[4]) >= int(value[8]):
                if value[9] <= 0:
                    threading.Thread(target=flashLed).start()
                    print("Alert",key,"is going high")
                    value[9]=4500000
                    alertScreen=1
                    threading.Thread(target=highALERTING, args=(0,key)).start()



#********************
#********************
#####################
#                   #
#Display            #
#   Threads         #
##################### 
#********************
#********************
   
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

def highlightbootDisplay():
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]

    if bootState['adc'][1]=="fail":
        faildot="."*bootState['adc'][0]
        draw.text((40,40),"ADC", fill = "WHITE", font=font)
        draw.text((150,40),".....", fill = "WHITE", font=font)
        draw.text((150,40),faildot, fill = "RED", font=font)
        if bootState['adc'][0]==5:
            draw.text((40,40),"ADC", fill = "RED", font=font)
    else:
        faildot="."*bootState['adc'][0]
        draw.text((40,40),"ADC", fill = "GREEN", font=font)
        draw.text((150,40),".....", fill = "WHITE", font=font)
        draw.text((150,40),faildot, fill = "GREEN", font=font)
        
        
    if bootState['elm'][1]=="fail":
        faildot="."*bootState['elm'][0]
        draw.text((40,93),"ELM", fill = "WHITE", font=font)
        draw.text((150,93),".....", fill = "WHITE", font=font)
        draw.text((150,93),faildot, fill = "RED", font=font)
        if bootState['elm'][0]==5:
            draw.text((40,93),"ELM", fill = "RED", font=font)
    else:
        faildot="."*bootState['elm'][0]
        draw.text((40,93),"ELM", fill = "GREEN", font=font)
        draw.text((150,93),".....", fill = "WHITE", font=font)
        draw.text((150,93),faildot, fill = "GREEN", font=font)
        
        
    if bootState['obd'][1]=="fail":
        faildot="."*bootState['obd'][0]
        draw.text((40,145),"OBD", fill = "WHITE", font=font)
        draw.text((150,145),".....", fill = "WHITE", font=font)
        draw.text((150,145),faildot, fill = "RED", font=font)
        if bootState['obd'][0]==5:
            draw.text((40,145),"OBD", fill = "RED", font=font)
    else:
        faildot="."*bootState['obd'][0]
        draw.text((40,145),"OBD", fill = "GREEN", font=font)
        draw.text((150,145),".....", fill = "WHITE", font=font)
        draw.text((150,145),faildot, fill = "GREEN", font=font)

    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)



#********************
#********************
#####################
#                   #
#Display/menu       #
#   Threads         #
##################### 
#********************
#********************

def menuDisplay(currentMenu,menu):
    encoder = rotaryio.IncrementalEncoder(seesaw)
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
    encoder = rotaryio.IncrementalEncoder(seesaw)
    seesaw.set_encoder_position(0)
    global ingauge
    global alertScreen
    global breadCrumb
    button_held = False
    oldEncValue=0
    newEncValue=0
    ingauge =0
    while alertScreen ==0:
       
       newEncValue=-encoder.position
       if newEncValue > oldEncValue and 5000 >= newEncValue:
           item-=2
           oldEncValue=newEncValue
          
       if newEncValue < oldEncValue and -5000 <= newEncValue:
           item+=2
           oldEncValue=newEncValue
          
       if item == (len(menu)):
           item=0
       if item <0:
           item=(len(menu))-2
       breadCrumb=(item,menu)
       menuDisplay(item,menu)

        
       if not button.value and not button_held:
           button_held = True
       if button.value and button_held:
           button_held = False
           breadCrumb=(item,menu)
           doaction(item,menu)

def doaction(item,menu):
    global ingauge
    ingauge=1
    time.sleep(.2)
    if (menu[item]=="Gauges"):
        menuloop(0,gaugemenu)
    if (menu[item]=="ECU"):
        menuloop(0,ecumenu)
    if (menu[item] == "Config"):
        menuloop(0,configmenu)
    highlightDisplay("Loading",menu[item])
    eval(menu[item+1] + "()")
    
def backtotop1():
    menuloop(0,topmenu)
def backtotop2():
    menuloop(2,topmenu)
def backtotop3():
    menuloop(4,topmenu)



#********************
#********************
#####################
#                   #
#Gauge functions    #
#                   #
##################### 
#********************
#********************

def ENGINE_LOAD():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["ENGINE_LOAD"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Load", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def COOLANT_TEMP():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["COOLANT_TEMP"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((60,26),"Water", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def FUEL_PRESSURE():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["FUEL_PRESSURE"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Fuel Pres", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def INTAKE_PRESSURE():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["INTAKE_PRESSURE"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Intake", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def RPM():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["RPM"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"RPM", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1]) 

def SPEED():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["SPEED"][4])+"Km",font=gfont, fill="WHITE")
        draw.text((60,26),"Speed", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def TIMING_ADVANCE():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["TIMING_ADVANCE"][4])+"°",font=gfont, fill="WHITE")
        draw.text((60,26),"Timing", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def INTAKE_TEMP():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["INTAKE_TEMP"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((60,26),"Intake", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def MAF():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["MAF"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"MAF", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def THROTTLE_POS():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["THROTTLE_POS"][4])+"%",font=gfont, fill="WHITE")
        draw.text((60,26),"Throttle", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def RUN_TIME():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["RUN_TIME"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Running", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def FUEL_LEVEL():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["FUEL_LEVEL"][4])+"%",font=gfont, fill="WHITE")
        draw.text((60,26),"Fuel", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def BAROMETRIC_PRESSURE():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["BAROMETRIC_PRESSURE"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Pressure", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def AMBIANT_AIR_TEMP():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["AMBIANT_AIR_TEMP"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((60,26),"Outside", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def FUEL_RATE():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["FUEL_RATE"][4]),font=gfont, fill="WHITE")
        draw.text((60,26),"Fuel Rate", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def OIL_TEMP():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((42,90),str(gaugeItems["OIL_TEMP"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((60,26),"Oil", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1]) 

def OIL_PRESSURE_ADC():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((40,95),str(gaugeItems["OIL_PRESSURE_ADC"][4])+" psi",font=gfont, fill="WHITE")
        draw.text((45,26),"Oil Pres", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                
                menuloop(breadCrumb[0],breadCrumb[1]) 
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1]) 
                button_held=False

def BOOST_ADC():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((53,95),str(gaugeItems["BOOST_ADC"][4]),font=gfont, fill="WHITE")
        draw.text((50,26),"Boost", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def BLOCK_TEMP1_ADC():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((53,95),str(gaugeItems["BLOCK_TEMP1_ADC"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((50,26),"Block", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1]) 

def BLOCK_TEMP2_ADC():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((53,95),str(gaugeItems["BLOCK_TEMP2_ADC"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((50,26),"Heads", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                print("trying to exit")
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])
 
def CABIN_TEMP_i2c():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((57,90),str(gaugeItems["CABIN_TEMP_i2c"][4])+"°C",font=gfont, fill="WHITE")
        draw.text((64,26),"Inside", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  
                
def ALTITUDE_i2c():
    button_held=False
    global alertScreen
    while alertScreen==0:
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        draw.text((57,90),str(gaugeItems["ALTITUDE_i2c"][4])+"m",font=gfont, fill="WHITE")
        draw.text((64,26),"Altitude", font=font, fill="WHITE") 
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])  

def QUAD_GAUGE():
    watch_RPM=2000  #### need to check for obd and fill value if no obd
    watch_OIL=20    #### need to check for obd and fill value if no obd
    button_held=False
    global alertScreen
    while alertScreen==0:     
        try:
            RPM=gaugeItems["RPM"][4]
            oilTemp=gaugeItems["OIL_TEMP"][4]
        except KeyError:
            RPM=0
            oilTemp=0

        oilPSI=gaugeItems["OIL_PRESSURE_ADC"][4]
        boost=gaugeItems["BOOST_ADC"][4]
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        if int(watch_RPM)>6000:
            if (len(str(watch_RPM))==3):
                draw.text((84,20),str(RPM), font=font, fill="RED")
            else:
                draw.text((74,20),str(_RPM), font=font, fill="RED")
        else:
            if (len(str(watch_RPM))==3):
                draw.text((84,20),str(RPM), font=font, fill="WHITE")
            else:
                draw.text((74,20),str(RPM), font=font, fill="WHITE")

        draw.text((108,67),"RPM",font=font3,fill="RED")
        draw.line([(0,84),(250, 84)], fill ="RED",width = 3)

        draw.text((25,90),str(oilTemp)+"°",font=font,fill="WHITE")
        draw.text((30,137),"Oil Temp", font=font3,fill="RED")

        draw.line([(120,84),(120,153)],fill="RED", width=3)

        draw.text((130,90),str(oilPSI), font=font, fill="WHITE")
        draw.text((199,110),"psi",font=font2, fill="WHITE")
        draw.text((160,137),"Oil Pres", font=font3,fill="RED")

        draw.line([(0,153),(240,153)],fill="RED", width=3)

        draw.text((100,160),"BOOST",font=font3,fill="RED")

        if (len(str(boost))==2):
            draw.text((90,175),str(boost), font=gfont,fill="WHITE")
        elif (len(str(boost))==3):
            draw.text((80,175),str(boost), font=gfont, fill="WHITE")
        else:
            draw.text((105,175),str(boost), font=gfont, fill="WHITE")

        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)


        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])

def TEMP_GAUGE():  
    button_held=False
    global alertScreen
    while alertScreen==0:     
        
        watch_OIL=gaugeItems["CABIN_TEMP_i2c"][4]
        oilPSI=gaugeItems["OIL_PRESSURE_ADC"][4]
        boost=gaugeItems["BOOST_ADC"][4]
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]
        if int(watch_OIL)>99:
            if (len(str(watch_OIL))==2):
                draw.text((105,20),str(watch_OIL), font=font, fill="RED")
            else:
                draw.text((84,20),str(watch_OIL), font=font, fill="RED")
        else:
            if (len(str(watch_OIL))==2):
                draw.text((105,20),str(watch_OIL), font=font, fill="WHITE")
            else:
                draw.text((84,20),str(watch_OIL), font=font, fill="WHITE")

        draw.text((100,67),"Oil Temp",font=font3,fill="RED")
        draw.line([(0,84),(250, 84)], fill ="RED",width = 3)

        draw.text((25,90),str(gaugeItems["BLOCK_TEMP2_ADC"][4])+"°",font=font,fill="WHITE")
        draw.text((30,137),"Head Temp", font=font3,fill="RED")

        draw.line([(120,84),(120,153)],fill="RED", width=3)

        draw.text((150,90),str(gaugeItems["BLOCK_TEMP1_ADC"][4])+"°", font=font, fill="WHITE")
        draw.text((160,137),"Block Temp", font=font3,fill="RED")

        draw.line([(0,153),(240,153)],fill="RED", width=3)
        draw.text((95,160),"Water Temp",font=font3,fill="RED")

        if (len(str(boost))==2):
            draw.text((90,175),str(boost), font=gfont,fill="WHITE")
        elif (len(str(boost))==3):
            draw.text((80,175),str(boost), font=gfont, fill="WHITE")
        else:
            draw.text((105,175),str(boost), font=gfont, fill="WHITE")

        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)


        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            if alertScreen ==1:
                alertScreen =0
                menuloop(breadCrumb[0],breadCrumb[1])
                button_held=False
            else:
                button_held = False
                menuloop(breadCrumb[0],breadCrumb[1])



#********************
#********************
#####################
#                   #
#config items       #
#                   #
##################### 
#********************
#********************

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
    button_held=False
    while tempcount <=10:
        if not button.value and not button_held:
            button_held = True
        if button.value and button_held:
            button_held = False
            menuloop(4,configmenu)
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

def update():
    highlightDisplay("Updating","Car Guage")
    repo.pull()
   
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
    menuloop(2,configmenu)

def steinhart_temperature_C(r, Ro=10000.0, To=25.0, beta=3984.0):
    import math
    steinhart = math.log(r / Ro) / beta      # log(R/Ro) / beta
    steinhart += 1.0 / (To + 273.15)         # log(R/Ro) / beta + 1/To
    steinhart = (1.0 / steinhart) - 273.15   # Invert, convert to C
    return steinhart

def ecu_read():
    print("doing ECU read")

def ecu_reset():
    print("doing ECU reset")
    
def muteBuzzer():
    global buzzerMute
    if buzzerMute == 1:
        buzzerMute =0
        highlightDisplay("Unmuted","Buzzer")
        time.sleep(5)
        menuloop(0,configmenu)
        
    else:
        buzzerMute =1
        highlightDisplay("Muted","Buzzer")
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
    time.sleep(3)  
    connectADC()
    connectELM()
    connectOBD()
    OBDcleanup()


def OBDcleanup():
    print("Initial Gauge Items: ",len(gaugeItems))
    if bootState["adc"][2]==0:
        cleanupMenu()
        return
    if bootState["adc"][2] ==1:
        for key,value in gaugeItems.items():
            if value[6] =="adc":
                value[2]=1
    if bootState["obd"][2] ==1:
        for key,value in gaugeItems.items():
            value[2]=1
 
    if bootState["obd"][2]==0:
        cleanupMenu()
        return
    cleanupMenu()

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
    print("Final Gauge Items: ",round((len(gaugemenu)-2)/2))



#********************
#********************
#####################
#                   #
#MAIN AREA          #
#                   #
##################### 
#********************
#********************

firstBoot()
try:
    threading.Thread(target=menuloop, args=(0,topmenu)).start()
    if bootState["obd"][2]==1:
        threading.Thread(target=obdTHREAD).start()
    if bootState["adc"][2]==1:
        threading.Thread(target=adcTHREAD).start()
    threading.Thread(target=alertTHREAD).start()

except:
    print("failed starting threads")
