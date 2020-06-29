import time
import board
import adafruit_dht
import sqlite3
from gpiozero import LED

def real_feel(T, rh):
    if (T >= 80):
        return -42.379 + (2.04901523 * T) + (10.14333127 * rh) - (0.22475541 * T * rh) - (6.83783 * 10**-3 * T**2) - (5.481717 * 10**-2 * rh**2) + (1.22874 * 10**-3 * T**2 * rh) + (8.5282 * 10**-4 * T * rh**2) - (1.99 * 10**-6 * T**2 * rh**2) 
    else:
        return 0.5 * (T + 61.0 + ((T-68.0)*1.2) + (rh*0.094)) 

def test_real_feel(T, rh):   
    print ("Test RealFeel ({:.1f} : {:.1f}% = {:.1f})".format(T, rh, real_feel(T, rh)))

def convert_to_f(Tc):
    return Tc * (9 / 5) + 32

def clear_db():
    conn = sqlite3.connect('/home/pi/Database/WeatherStation/WeatherStation.db')
    conn.execute("DELETE FROM INDOOR_SENSOR")
    conn.commit()
    conn.close()
    
def insert_to_db(temp, humi, realFeel):
    conn = sqlite3.connect('/home/pi/Database/WeatherStation/WeatherStation.db')
    conn.execute("INSERT INTO INDOOR_SENSOR (TEMP, HUMIDITY, REAL_FEEL, CREATE_DATE) \
      VALUES (" + str(temp) + ", " + str(humi) + ", " + str(realFeel) + ", datetime('now'))");
    conn.commit()
    conn.close()


#test_real_feel(75, 75)

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D4)
#led = LED(17)

clear_db()
while True:
    try:
        #led.on()
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = convert_to_f(temperature_c)
        humidity = dhtDevice.humidity
        realFeel = round(real_feel(temperature_f, humidity),1)
        insert_to_db(round(temperature_f,1), humidity, round(realFeel,1))
        print(
            "Temp: {:.1f} F / {:.1f} C    Humidity: {}%    RealFeel {:.1f} F ".format(
                temperature_f, temperature_c, humidity, realFeel
            ), end='\r'
        )
         
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        #print(error.args[0])
        continue
 
    time.sleep(50.0)

