# -*- encoding: UTF-8

# Basic script to read sensors  on the RasPi SPI bus
# using MCP3008 ADC and publish it to Cosm
# Written by Daniel Bergey & Christalee Bieber

import eeml, serial, time, datetime, csv, os
import spidev
from math import log
import json

# init SPI
chip0 = spidev.SpiDev()
chip0.open(0,0)
chip1 = spidev.SpiDev()
chip1.open(0,1)

# Cosm credentials
config = json.loads(open('config.json').read())
API_KEY = config['API_KEY']
API_URL = config['API_URL']
pac = eeml.Cosm(API_URL, API_KEY)

# init local CSV logging
if os.path.exists("berrybasket.csv"):
    logfile = open("berrybasket.csv", "ab")
    logwriter = csv.writer(logfile)
else:
    logfile = open("berrybasket.csv", "wb")
    logwriter = csv.writer(logfile)
    logwriter.writerow(['Timestamp', 'Channel 0 (Celsius)', 'Channel 1', 'Channel 2', 'Channel 3', 'Channel 4', 'Channel 5', 'Channel 6', 'Channel 7', 'Channel 8', 'Channel 9', 'Channel 10', 'Channel 11', 'Channel 12', 'Channel 13', 'Channel 14', 'Channel 15'])

# adc_value range specific to MCP3008 (or 3004)
def RfromMCP(adc_value, R0=10000):
    """Assumes that sensor is connected to MCP's Vref,
    and matched resistor is connected to ground.
    V_{ADC} = V_+ \frac{R_0}{R_S+R_0}
    R_S = R_0 \(\frac{V_+}{V_{ADC}}-1\)
    adc_value = 1023 \frac{V_{ADC}}{V_+}"""
    if adc_value==0:
        return 2000*R0
    else:
        return R0*(1023.0/adc_value -1)

# specific to thermistor used
# TODO document which thermistor this is for
def K_thermistorR(R):
    Rref = 12000
    A1 = 3.354E-3
    B1 = 2.744E-4
    C1 = 3.667E-6
    D1 = 1.375E-7

    epsilon = 1e-5
    lnR = log((R+epsilon)/Rref)
  
    return 1/(A1 + B1*lnR + C1*lnR**2 + D1*lnR**3)

# specific to thermistor used
def C_thermistorR(R):
    """returns Temperature in degrees °C,
given Resistance R in Ohms"""
    return K_thermistorR(R) - 273.25

# unit classes for Cosm API
class Volt(eeml.Unit):
    def __init__(self):
        eeml.Unit.__init__(self, 'Volt', 'basicSI', 'V')

class Ohm(eeml.Unit):
    def __init__(self):
        eeml.Unit.__init__(self, 'Volt', 'basicSI', u'Ω')

# from https://github.com/jerbly/Pi/blob/master/raspi-adc-pot.py
def readadc(chip, channel):
    """read channel ADCNUM of the MCP3008 chip"""
    if ((channel > 7) or (channel < 0)):
        return -1
    r = chip.xfer2([1,(8+channel)<<4,0])
    adcout = ((r[1]&3) << 8) + r[2]
    return adcout

if __name__=="__main__":
    while True:
        thermlog = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M')]
        for chnum, chip in enumerate((chip0, chip1)):
            for channel in xrange(8):
                # seperate these calls for debugging
                raw_thermR = readadc(chip, channel)
                thermR = RfromMCP(raw_thermR)
                thermC = C_thermistorR(thermR)
                thermlog.append("{0:.1f}".format(thermC))
                # build eeml structure
                pac.update([eeml.Data(chnum*8 + channel, thermC, unit=eeml.Celsius())])
        try:
            # talk to Cosm server
            pac.put()
        except:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M pac.put() failed'))
        logwriter.writerow(thermlog)
        time.sleep(10)
