#!/usr/bin/env python
from collections import Counter
from bitstring import ConstBitStream

import sys
import time
import pigpio

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
          if (diff > 600 and diff < 1000):
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
              
          if (ltdcount == 8): #start
              passNum += 1
              #print("Pass = {}".format(passNum))
              ltdcount = 0
              start = True
      
      elif (start):
          pulses += 1
          diffarr.append(str(diff))
          
          if (level == 0 and diff > 350):
              bitarr.append("1")
          elif (level == 0 and diff <= 350):
              bitarr.append("0")
                  
          if (pulses == 80):
              start = False
              pulses = 0
              #print("diffarr = {}".format(", ".join(diffarr)))
              #print("bitarr = {}".format("".join(bitarr)))
              bitarrs.append("".join(bitarr))
              bitarr = []
              diffarr = []
                  
   last[GPIO] = tick

def findMostCommon(strList):
    counter = Counter(strList)
    mostCommon = counter.most_common(1)
    return mostCommon

def parseBitArray(bitArray):
    bits = ConstBitStream(bin=bitArray)
    bits.pos = 12  
    t = bits.read('int:12')
    temp = (t/10-50) * 1.8 + 32
    humi = bits.read('int:8')
    print("temp = {}, humi = {}".format(round(temp,1), humi))
    
pi = pigpio.pi()

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
