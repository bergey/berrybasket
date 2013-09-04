# -*- encoding: UTF-8

# Basic script to read sensors  on the RasPi SPI bus
# using MCP3008 ADC and publish it to Cosm
# Written by Daniel Bergey & Christalee Bieber

import serial, time, datetime, os
import spidev
from math import log
import json

# init SPI
chip0 = spidev.SpiDev()
chip0.open(0,0)
chip1 = spidev.SpiDev()
chip1.open(0,1)

config = json.loads(open('config.json').read())

# Cosm credentials
if 'cosm' in config:
    import eeml
    API_KEY = config['cosm']['API_KEY']
    API_URL = config['cosm']['API_URL']
    pac = eeml.Cosm(API_URL, API_KEY)
else:
    pac = None

# init local CSV logging
if 'logfile' in config:
    import csv
    logfilename = config['logfile']
    if os.path.exists(logfilename):
        logfile = open(logfilename, "ab")
        logwriter = csv.writer(logfile)
    else:
        logfile = open(logfilename, "wb")
        logwriter = csv.writer(logfile)
        logwriter.writerow(['Timestamp', 'Channel 0 (Celsius)'] + ['Channel ' + str(n) for n in xrange(1,16)])
else:
    logwriter = None

# credentials to write to Thingspeak
if 'thingspeak' in config:
    import thingspeak
    thing_channel_1 = thingspeak.channel(config['thingspeak']['write_key_1'])
    if 'write_key_2' in config['thingspeak']:
        thing_channel_2 = thingspeak.channel(config['thingspeak']['write_key_2'])
    else:
        thing_channel_2 = None
else:
    thing_channel_1 = None

# adc_value range specific to MCP3008 (or 3004)
def RfromMCP(adc_value, R0=10000):
    """Assumes that sensor is connected to MCP's Vref,
    and matched resistor is connected to ground.
    V_{ADC} = V_+ \frac{R_0}{R_S+R_0}
    R_S = R_0 \(\frac{V_+}{V_{ADC}}-1\)
    adc_value = 1023 \frac{V_{ADC}}{V_+}
    adc_value can be 0 when the channel is not connected (floating)
    We don't want to throw an exception in case other  channels are connected
    adc_value < 1 implies R >> R0, so we make up such a value
    It's high enough to indicate that it shouldn't be taken literally"""
    if adc_value==0:
        return 2000*R0
    else:
        return R0*(1023.0/adc_value -1)

# specific to thermistor used
def K_thermistorR(R):
    """K_thermistorR calculates the temperature in K of a
    NTCLE100E3 thermistor with R=12kΩ at 25°C,
    using equation and coefficients from the datasheet."""
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
    """returns Temperature in degrees Celsius (°C),
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
    """read channel CHANNEL  of the MCP3008
    CHIP should be an SpiDev object"""
    if ((channel > 7) or (channel < 0)):
        return -1
    r = chip.xfer2([1,(8+channel)<<4,0])
    adcout = ((r[1]&3) << 8) + r[2]
    return adcout

if __name__=="__main__":
    while True:
        # read all the channels
        readings = []
        for chip in (chip0, chip1):
            for channel in xrange(8):
                # seperate these calls for debugging
                raw_thermR = readadc(chip, channel)
                thermR = RfromMCP(raw_thermR)
                thermC = C_thermistorR(thermR)
                readings.append(thermC)

        if pac:
            for chnum, t in enumerate(readings): # build Cosm eeml structure
                pac.update([eeml.Data(chnum, t, unit=eeml.Celsius())])
            try:
                # talk to Cosm server
                pac.put()
            except:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M pac.put() failed'))

        if logwriter: # CSV log
            thermlog = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M')]
            for r in readings:
                thermlog.append("{0:.1f}".format(r))
            logwriter.writerow(thermlog)

        if thing_channel_1: # thingspeak.com
            thing_channel_1.update(readings[:8])
        if thing_channel_2:
            thing_channel_2.update(readings[8:])

        time.sleep(10)
