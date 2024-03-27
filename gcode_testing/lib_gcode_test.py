import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200)
time.sleep(2)
# ser.write(str.encode("G28\r\n"))
command_dict = {
    'home': 'G28 X Y',
    'abs_center' : 'G0 X127 Y90 Z220 F3600',
    'center' : 'G0 X127 Y90 F3600',
    'pos': 'M114',
}
while True:
    input_command = input("Enter a GCODE command: ")
    if input_command in command_dict:
        input_command = command_dict[input_command]
    ser.write(str.encode(input_command + "\r\n"))
    time.sleep(2)
    cc=str(ser.readline())
    print(cc)
ser.close()
