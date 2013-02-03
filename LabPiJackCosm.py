# -*- encoding: UTF-8

# Basic script to read data from AIN0 and AIN2 on the LabJack and publish it to Cosm
# Written by Daniel Bergey & Christalee Bieber

import eeml, serial, time, u3, datetime, csv, os
from math import log

API_KEY = '33AIUxH1xC38tTBSPjQL3n9LileSAKxaZktlL1pwdldCST0g'
API_URL = 84597
pac = eeml.Cosm(API_URL, API_KEY)

d = u3.U3()
AIN0 = 0
AIN1 = 2
AIN2 = 4

if os.path.exists("LabPiJackCosm.csv"):
    logfile = open("LabPiJackCosm.csv", "ab")
    logwriter = csv.writer(logfile)
else: 
    logfile = open("LabPiJackCosm.csv", "wb")
    logwriter = csv.writer(logfile)
    logwriter.writerow(['Timestamp', 'Photoresistor (Ohms)', 'Thermistor (Celsius)'])

def RfromV(V, V0=5, R0=10000):
    """V in Volts, V0 in Volts, R0 in Ohms,
    assuming R0 is between AIN and V0,
    R to be returned is between AIN and Gnd"""
  
    return (V*R0) / (V0 - V)
  
def K_thermistorR(R):
    Rref = 12000
    A1 = 3.354E-3
    B1 = 2.744E-4
    C1 = 3.667E-6
    D1 = 1.375E-7
  
    lnR = log(R/Rref)
  
    return 1/(A1 + B1*lnR + C1*lnR**2 + D1*lnR**3)
  
def C_thermistorR(R):
    """returns Temperature in degrees °C,
    given Resistance R in Ohms"""
  
    return K_thermistorR(R) - 273.25

class Volt(eeml.Unit):
    def __init__(self):
        eeml.Unit.__init__(self, 'Volt', 'basicSI', 'V')
  
class Ohm(eeml.Unit):
    def __init__(self):
        eeml.Unit.__init__(self, 'Volt', 'basicSI', u'Ω')

while True:
    V0 = d.readRegister(AIN1)
    photoR = RfromV(d.readRegister(AIN0), V0)
    thermR = C_thermistorR(RfromV(d.readRegister(AIN2), V0))
    pac.update([eeml.Data('Photoresistor', photoR, unit=Ohm()), eeml.Data('Thermistor', thermR, unit=eeml.Celsius())])
    try:
	pac.put()
    except:
	print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M pac.put() failed'))
    logwriter.writerow([datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), photoR, thermR])
    time.sleep(600)

