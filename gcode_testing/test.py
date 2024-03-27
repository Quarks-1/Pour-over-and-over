import serial

ser = serial.Serial("/dev/ttyUSB0", 115200)
ser.write("G28\n")
ser.write("M114\n")
ser.read_all()
