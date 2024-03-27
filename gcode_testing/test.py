import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200)
time.sleep(2)

for command in ["G28", "M114"]:
    ser.write(str.encode(command + "\r\n"))
    time.sleep(1)
print(ser.read_all().decode())
ser.close()
