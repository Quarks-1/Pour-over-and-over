# Importing Libraries 
import serial 
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 

while True:
    # take pump on or pump off input
    try:
        command = input("Enter pump on or pump off: ")
    except KeyboardInterrupt:
        break
    if command == 'on':
        command = f'pumpon/255'
    elif command == 'off':
        command = 'pumpon/0'
    else:
        command = f'pumpon/{command}'
    # send command to arduino
    try:
        written = arduino.write(str.encode(command))
        print('wrote: ', written)
    except serial.SerialException:
        print('WARNING: ARDUINO NOT CONNECTED')
        break
arduino.close()