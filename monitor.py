#!/usr/bin/env python

# monitor.py
# 2016-09-17
# Public Domain

# monitor.py          # monitor all GPIO
# monitor.py 23 24 25 # monitor GPIO 23, 24, and 25

import sys
import time
import pigpio

last = [None]*32
cb = []

def cbf(GPIO, level, tick):
   global ltdcount
   global ltdEndCount
   global start
   global end
   global bitarr
   global diffarr
   
   try:
       foo = start
   except NameError:
       start = False
   
   try:
       foo = bitarr
   except NameError:
       bitarr = []
       
   try:
       foo = diffarr
   except NameError:
       diffarr = []
   
   if last[GPIO] is not None:
      diff = pigpio.tickDiff(last[GPIO], tick)
      #print("G={} l={} d={}".format(GPIO, level, diff))
      diffarr.append(diff)
      
      if (not start):
          if (diff > 800 and diff < 1000):
             ltdcount += 1
          else:
             ltdcount = 0
        
          if (ltdcount == 8):
              start = True
              ltdEndCount = 0
              
      elif (start):
          if (diff > 800 and diff < 1000):
              ltdEndCount += 1
          
          if (ltdEndCount == 4):
              print("diffarr = {}".format("".join(diffarr)))
              print("bitarr = {}".format(bitarr))
              start = False
              bitarr = []
              diffarr = []
              ltdEndCount = 0
              ltdcount = 0
              
          if (ltdEndCount == 0):
              if (level == 0 and diff > 400):
                  bitarr.append("1")
              elif (level == 0 and diff < 300):
                  bitarr.append("0")
                     
   last[GPIO] = tick
   
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

