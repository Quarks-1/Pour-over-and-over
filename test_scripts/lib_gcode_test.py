import serial
import time

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
time.sleep(2)
# ser.write(str.encode("G28\r\n"))
command_dict = {
    'home': 'G28 X Y',
    'abs_center' : 'G0 X127 Y90 Z220 F3600',
    'center' : 'G0 X127 Y90 F3600',
    'pos': 'M114',
}
recording = []
record = False
while True:
    input_command = input("Enter a GCODE command: ")
    if input_command in command_dict:
        input_command = command_dict[input_command]
    elif input_command == "record":
        record = not record
        if record:
            print("Recording...")
        else:
            print("Stopped recording.")
    elif input_command == 'undo':
        recording.pop()
        continue
    elif input_command == 'clear':
        recording = []
        continue
    elif input_command == 'exit':
        break
    
    if record:
        recording.append(input_command)
    
    ser.reset_input_buffer()
    ser.write(str.encode(input_command + "\r\n"))
    time.sleep(2)
    cc=str(ser.readline())
    # while cc == "b'echo:busy: processing\n'" or cc == b'ok\n':
    #     cc=str(ser.readline())
    print(cc)
    

print(f'Recording: {recording}')
print("Exiting...")
ser.close()
