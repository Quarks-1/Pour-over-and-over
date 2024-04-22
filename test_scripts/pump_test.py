# Importing Libraries 
import serial 
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 

while True:
    # take pump on or pump off input
    command = input("Enter pump on or pump off: ")
    if command == 'on':
        command = 'pumpon/255'
    elif command == 'off':
        command = 'pumpoff'
    elif command == '':
        continue
    else:
        command = f'pumpon/{command}'
    # send command to arduino
    arduino.write(str.encode(command))