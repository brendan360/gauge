import board
import busio
import time
i2c = busio.I2C(board.SCL, board.SDA)
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
ads = ADS.ADS1115(i2c)
import adafruit_htu31d
htu = adafruit_htu31d.HTU31D(i2c)




#32737

def steinhart_temperature_C(r, Ro=10000.0, To=25.0, beta=3984.0):
    import math
    steinhart = math.log(r / Ro) / beta      # log(R/Ro) / beta
    steinhart += 1.0 / (To + 273.15)         # log(R/Ro) / beta + 1/To
    steinhart = (1.0 / steinhart) - 273.15   # Invert, convert to C
    return steinhart




while True:
    time.sleep(3)
    temperature, relative_humidity = htu.measurements
    print("Temperature: %0.1f C" % temperature)
    chan1 = AnalogIn(ads, ADS.P0)
    chan2 = AnalogIn(ads, ADS.P1)
    chan2 = AnalogIn(ads, ADS.P2)
    
    old_min=1088
    old_max=32767
    new_min=0
    new_max=150
    adcoil=chan2.value

    oilpsi=((adcoil - old_min)/(old_max-old_min))*(new_max-new_min)+new_min
    
    oilpsi=round(oilpsi)

    print("Oil PSI: {}psi".format(oilpsi))
    print(chan2.value)
    print("-----------------------------")
    thermistor1 = chan1
    R1 = 10000 / (41835/thermistor1.value - 1)
    print('Thermistor1 resistance: {} ohms'.format(R1))
    print('R1 Temp:',round(steinhart_temperature_C(R1)))
    thermistor2 = chan2
    R2 = 10000 / (41835/thermistor1.value - 1)
    print('Thermistor2 resistance: {} ohms'.format(R2))
    print('R2 temp:',round(steinhart_temperature_C(R2)))
    print("-----------------------------")
    print()
    print()
