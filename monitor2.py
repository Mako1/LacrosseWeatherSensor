#!/usr/bin/env python
from collections import Counter
from bitstring import ConstBitStream

import sys
import time
import pigpio
import sqlite3

BAD_READ = "0000000000000000000000000000000000000000"
PREEMBLE_LOW = 600
PREEMBLE_HIGH = 1000
BIT_ONE_HIGH = 350
BIT_ZERO_HIGH = 350
PULSES = 80

last = [None]*32
cb = []

def cbf(GPIO, level, tick):
   global ltdcount
   global passNum
   global start
   global pulses
   global diffarr
   global isEnd
   global bitarr
   global bitarrs
   
   try:
       foo = ltdcount
   except NameError:
       ltdcount = 0
   
   try:
       foo = passNum
   except NameError:
       passNum = 0
    
   try:
       foo = start
   except NameError:
       start = False
   
   try:
       foo = pulses
   except NameError:
       pulses = 0
   
   try:
       foo = diffarr
   except NameError:
       diffarr = []
   
   try:
       foo = isEnd
   except NameError:
       isEnd = False
       
   try:
       foo = bitarr
   except NameError:
       bitarr = []
       
   try:
       foo = bitarrs
   except NameError:
       bitarrs = []
       
   if last[GPIO] is not None:
      diff = pigpio.tickDiff(last[GPIO], tick)
      #print("G={} l={} d={}".format(GPIO, level, diff))
      
      if (not start):
          if (diff > PREEMBLE_LOW and diff < PREEMBLE_HIGH):
              ltdcount += 1
              diffarr.append(str(diff))
          else:
              if (isEnd):
                  print("{} passes complete".format(passNum))
                  isEnd = False
                  passNum = 0               
                  mostCommon = findMostCommon(bitarrs)
                  print("Most common bit array = {}".format(mostCommon))
                  parseBitArray(mostCommon[0][0])
                  bitarrs = []
                  
              if (passNum >= 10 and ltdcount == 3):
                  isEnd = True
              
              ltdcount = 0
              diffarr = []
              #passNum = 0
              
          if (ltdcount == 8): #start
              passNum += 1
              #print("Pass = {}".format(passNum))
              ltdcount = 0
              start = True
      
      elif (start):
          pulses += 1
          diffarr.append(str(diff))
          
          if (level == 0 and diff >= BIT_ONE_HIGH):
              bitarr.append("1")
          elif (level == 0 and diff < BIT_ZERO_HIGH):
              bitarr.append("0")
                  
          if (pulses == PULSES):
              start = False
              pulses = 0
              #print("diffarr = {}".format(", ".join(diffarr)))
              #print("bitarr = {}".format("".join(bitarr)))
              bitarrs.append("".join(bitarr))
              bitarr = []
              diffarr = []
                  
   last[GPIO] = tick

def findMostCommon(strList):
    counter = Counter([s for s in strList if s != BAD_READ])
    mostCommon = counter.most_common(1)
    return mostCommon

def parseBitArray(bitArray):
    bits = ConstBitStream(bin=bitArray)
    bits.pos = 12  
    t = bits.read('int:12')
    temp = round((t/10-50) * 1.8 + 32,1)
    humi = bits.read('int:8')
    realFeel = round(real_feel(temp, humi),1)
    print("temp = {}, humi = {}, real feel = {}".format(temp, humi, realFeel))
    insert_to_db(temp, humi, realFeel)

def real_feel(T, rh):
    if (T >= 80):
        return -42.379 + (2.04901523 * T) + (10.14333127 * rh) - (0.22475541 * T * rh) - (6.83783 * 10**-3 * T**2) - (5.481717 * 10**-2 * rh**2) + (1.22874 * 10**-3 * T**2 * rh) + (8.5282 * 10**-4 * T * rh**2) - (1.99 * 10**-6 * T**2 * rh**2) 
    else:
        return 0.5 * (T + 61.0 + ((T-68.0)*1.2) + (rh*0.094)) 

def clear_db():
    conn = sqlite3.connect('/home/pi/Database/WeatherStation/WeatherStation.db')
    conn.execute("DELETE FROM OUTDOOR_SENSOR")
    conn.commit()
    conn.close()

def insert_to_db(temp, humi, realFeel):
    conn = sqlite3.connect('/home/pi/Database/WeatherStation/WeatherStation.db')
    conn.execute("INSERT INTO OUTDOOR_SENSOR (TEMP, HUMIDITY, REAL_FEEL, CREATE_DATE) \
      VALUES (" + str(temp) + ", " + str(humi) + ", " + str(realFeel) + ", datetime('now'))");
    conn.commit()
    conn.close()

pi = pigpio.pi()

clear_db()

if not pi.connected:
   exit()

if len(sys.argv) == 1:
   G = range(0, 32)
else:
   G = []
   for a in sys.argv[1:]:
      G.append(int(a))

print("Waiting for signal...")
for g in G:
   x = pi.callback(g, pigpio.EITHER_EDGE, cbf)
   cb.append(x)

try:
   while True:
      time.sleep(60)
except KeyboardInterrupt:
   print("\nTidying up")
   for c in cb:
      c.cancel()

pi.stop()
