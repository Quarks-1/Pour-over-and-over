import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200)
time.sleep(2)
# ser.write(str.encode("G28\r\n"))
for command in ["G28 X Z", "M114", "G1 X127 Y90 Z220 F3600", "G2 I20 J20","M114"]:
    ser.write(str.encode(command + "\r\n"))
    time.sleep(1)
while True:
     cc=str(ser.readline())
     print(cc)
ser.close()
