import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200)
time.sleep(2)
ser.write("G28\r\n")
time.sleep(1)
ser.write("M114\r\n")
time.sleep(1)
print(ser.read_all().decode())
ser.close()
