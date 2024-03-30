# Importing Libraries 
import serial 
import time 
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 

while True:
    # arduino.reset_input_buffer()
    time.sleep(0.05)
    data = arduino.readline() 
    # while data == b'':
    #     data = arduino.readline()
    print(data) # printing the value 
