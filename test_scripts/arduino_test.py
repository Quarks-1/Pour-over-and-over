# Importing Libraries 
import serial 
import time 
arduino = serial.Serial(port='/dev/ttyACM1', baudrate=9600, timeout=.1) 

while True:
    arduino.reset_input_buffer()
    time.sleep(0.05)
    data = arduino.readline() 
    # while data == b'':
    #     data = arduino.readline()
    # Decode byte string to a normal string
    decoded_str = data.decode('utf-8')
    if decoded_str == '':
        continue

    # Strip whitespace and newlines
    clean_str = decoded_str.strip()

    # Split the string based on '/'
    numbers = clean_str.split('/')

    result = (float(numbers[0]), float(numbers[1]))

    # Print the result
    print(result)
