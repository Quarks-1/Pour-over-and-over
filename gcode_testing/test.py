import serial

ser = serial.Serial("/dev/ttyUSB3", 115200)
ser.write("G28\n")
ser.write("M114\n")
ser.read_all()
