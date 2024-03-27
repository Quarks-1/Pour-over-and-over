import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200)
time.sleep(2)
# ser.write(str.encode("G28\r\n"))
command_dict = {
    'home': 'G28 X Z',
    'abs_center' : 'G1 X127 Y90 Z220 F3600',
    'center' : 'G1 X127 Y90 F3600',
}
while True:
    input_command = input("Enter a GCODE command: ")
    ser.write(str.encode(input_command + "\r\n"))
    time.sleep(1)
    cc=str(ser.readline())
    print(cc)
ser.close()
