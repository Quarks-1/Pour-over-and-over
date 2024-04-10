from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json, serial, time, math
from threading import Thread
from datetime import datetime, timedelta
from simple_pid import PID

# (pour type, water weight, flow rate, agitation level (low, medium, high))
class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'
    
    profile = None
    printer = None
    arduino = None
    stop = False
    
    x, y, z = 0, 0, 0
    steps = []
    gcodeSteps = []
    startTime = None
    pid = None
    heated = False
    

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

        # Connect to printer
        try:
            self.printer = printer()
        except serial.SerialException:
            printError('WARNING: PRINTER NOT CONNECTED')
            self.broadcast_message('Printer not connected. Please connect printer and reload page.')
            return
    
        try:
            self.arduino = serial.Serial(port='/dev/ttyACM1', baudrate=9600, timeout=.1) 
        except serial.SerialException:
            printError('WARNING: ARDUINO NOT CONNECTED')
            self.broadcast_message('Arduino not connected. Please connect Arduino and reload page.')
            return
        
        self.startTime = datetime.now()
        self.broadcast_message('Successfully connected to Printer and Arduino.')
        self.broadcast_message('start data feed')

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        if self.printer is not None:
            self.printer.close()
        else:
            printError('WARNING: PRINTER NOT CONNECTED')
            return

    def receive(self, **kwargs):
        if 'text_data' not in kwargs:
            printError('You must send text_data')
            return

        try:
            data = json.loads(kwargs['text_data'])
        except json.JSONDecoder:
            printError('invalid JSON sent to server')
            return
        if 'command' not in data:
            printError('command property not sent in JSON')
            return

        action = data['command']
        
        if action == 'profileSelect':
            if 'profile' not in data:
                printError('profile property not sent in JSON')
                return
            elif self.arduino is None or self.printer is None:
                printError('Printer or Arduino not connected')
                return
            
            self.profile = BrewProfile.objects.get(id=data['profile'])
            print(f'Profile selected: {self.profile}')
            pid = PID(70, 30, 500, setpoint=self.profile.water_temp)  # P=1.0, I=0.1, D=0.05, desired temperature=25°C
            pid.sample_time = 0.5  # Update every 1 second
            pid.output_limits = (0, 1)  # Output value will be between 0 and 1 (off/on)
            self.pid = pid
            Thread(target=self.startHeater).start()
            self.steps = parseSteps(self.profile.steps)
            return

        if action == 'startBrew':
            if not self.heated:
                self.broadcast_message('Heating water. Please wait...')
                return
            x, y, z = self.printer.currPos()
            self.gcodeSteps = parseTimes(self.steps, datetime.now())
            print(bcolors.OKBLUE + f'Current position: {x}, {y}, {z}' + bcolors.ENDC)
            self.broadcast_message('Starting brew...')
            Thread(target=self.startBrew).start()
            self.received_start(data)
            return

        if action == "stopBrew":
            self.received_stop(data)
            self.broadcast_message('Brew stopped.')
            self.stop = True
            return
        
        if action == "restartBrew":
            self.broadcast_message('Brew restarted.')
            self.stop = False
            # parse steps again
            self.steps = parseSteps(self.profile.steps)
            self.gcodeSteps = parseTimes(self.steps, self.startTime)
            self.received_restart(data)
            return
        if action == 'updateData':
            self.get_arduino_feed()
            return
        
        if action == 'tareScale':
            self.arduino.write(b'tare\n')
            print('taring')
            return

        printError(f'Invalid action property: "{action}"')

################## To be filled in #######################
    def received_start(self, data):
        return
        self.broadcast_data()
        
    def received_stop(self, data):
        return
        self.broadcast_data()
        
    def received_restart(self, data):
        return
        self.broadcast_data()
################################################

    def broadcast_data(self, data):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'data', 'data': data})
            }
        )
    
    def broadcast_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps({'type': 'message', 'message': message})
            }
        )
    def broadcast_event(self, event):
        self.send(text_data=event['message'])
    
    def get_arduino_feed(self):
        self.arduino.reset_input_buffer()
        time.sleep(0.05)
        decoded_str = ''
        while decoded_str == '':
            try:
                data = self.arduino.readline() 
            except serial.SerialException:
                continue
            decoded_str = data.decode('utf-8')
            if len(decoded_str.split('/')) == 2:
                break
            time.sleep(0.05)
        # Strip whitespace and newlines
        clean_str = decoded_str.strip()

        numbers = clean_str.split('/')
        if len(numbers) != 2:
            printError('Invalid data received from Arduino')
            print(f'Invalid data: {clean_str}')
            return
        # Convert strings to floats and perform division
        try:
            result = (float(numbers[0]), float(numbers[1]))
        except ValueError:
            printError('Invalid data received from Arduino')
            print(f'Invalid data: {clean_str}')
            return
        data_dict = {
            'weight': result[0],
            'temp': result[1],
        }
        self.broadcast_data(data_dict)
    
    # TODO: Test heating
    def startHeater(self):
        self.broadcast_message('Heating water. Please wait...')
        while True:
            try:
                # Read temperature from serial
                self.arduino.reset_input_buffer()
                line = self.get_arduino_feed()
                # control_heating('heating_on')
                if line and len(line.split(',')) == 2:  # If line is not empty
                    # print(f'Line: {line}')
                    current_temp = float(line.split(',')[1])
                    # print(f"Current Temperature: {current_temp}°F")
                    
                    # Compute PID output
                    control = self.pid(current_temp)
                    # Decide on the heating element state based on PID output
                    heating_on = control >= 0.5  # Example logic to turn heating on/off
                    # Send command to Arduino to control the heating element
                    self.arduino.write(b'1\n' if heating_on else b'0\n')
                    # Optional: Print the control decision
                    # print("Heating On" if heating_on else "Heating Off")
                    # Check to see if target temp reached
                    if current_temp >= self.profile.water_temp:
                        self.broadcast_message('Water heated. Starting brew...')
                        break
                time.sleep(0.05)
            except KeyboardInterrupt:
                print("Exiting...")
                break
            except ValueError:
                # In case of faulty serial data that cannot be converted to float
                print("Invalid data received.")
                continue
            except serial.SerialException:
                printError('Arduino error')
                continue
        self.heated = True
        return
        
        
    def startBrew(self):
        while True:
            # Check if current time is time for next step
            try:
                self.gcodeSteps[0][1]
            except IndexError:
                print('No more steps. Brew complete.')
                self.broadcast_message('Brew complete')
                return
            if datetime.now() >= self.gcodeSteps[0][1]:
                self.broadcast_message('Working on next step...')
                print(f'Working on command: {self.gcodeSteps[0][0]}')
                if 'Draw down' in self.gcodeSteps[0][0]:
                    self.broadcast_message('Draw down')
                    time.sleep(max(int((self.gcodeSteps[0][1] - datetime.now()).total_seconds()) - 1, 0))
                    self.gcodeSteps.pop(0)
                    continue
                else:
                    # Send gcode to printer
                    for command in self.gcodeSteps[0][0]:
                        # Check if command is circle
                        if 'I' in command:
                            [i, j, x, y] = [int(command.split('I')[1].split(' ')[0]), int(command.split('J')[1].split(' ')[0]), int(command.split('X')[1].split(' ')[0]), int(command.split('Y')[1].split(' ')[0])]
                            self.printer.arcFromCurr(i, j, x, y)
                        else:
                            self.printer.write(command)
                    time.sleep(0.05)
                    # Actuate pump
                    Thread(target=self.doPour, args=(self.gcodeSteps[0][2])).start()
                    # Remove step from list
                    self.gcodeSteps.pop(0)
                    # Sleep for command time
                    time.sleep(max(int((self.gcodeSteps[0][1] - datetime.now()).total_seconds()) - 1, 0))
                    # If no more steps, break out of loop
                    if len(self.gcodeSteps) == 0:
                        break
            # Check if stop command received
            # TODO: implement stop
            if self.stop:
                print('Stopping brew...')
                break
        print('Brew complete')
        self.broadcast_message('Brew complete')
        return

    def doPour(self, water_weight, pour_time):
        # data = (water weight, time)
        # Send signal to arduino
        self.arduino.write(f'pumpOn,{water_weight / pour_time}\n'.encode())
        time.sleep(pour_time)
        self.arduino.write(b'pumpOff\n')
        return

class printer:
    def __init__(self):
        self.center = [127, 115, 0]
        self.ser = serial.Serial("/dev/ttyUSB0", 115200)
        # home printer
        self.ser.write(str.encode("G28 X Y\r\n"))
        # time.sleep(2)
        # TODO: Change Z to proper value
        self.ser.write(str.encode("G0 X117 Y110 Z220 F3600\r\n")) # move to center
    
    def goto(self, x, y, z):
        self.ser.write(str.encode(f"G0 X{x} Y{y} Z{z} F3600\r\n"))
    
    def write(self, command):
        self.ser.write(str.encode(command + "\r\n"))
    
    def arcFromCurr(self, i, j, x, y):
        # Offset from center
        print(f'Current position: {x}, {y}, i: {i}, j: {j}')
        self.ser.write(str.encode(f"G0 X{x-i} Y{y-j} F3600\r\n"))
        # Draw circle
        self.ser.write(str.encode(f"G2 X{x-i} Y{y-j} I{i} J{j} F3600\r\n"))
        

    def currPos(self) -> list[int, int, int]:
        self.ser.reset_input_buffer()
        self.ser.write(str.encode("M114\r\n"))
        x, y, z = 0, 0, 0
        for val in self.ser.readline().decode('utf-8').split(' '):
            if 'X' in val:
                x = int(val.strip('X:').split('.')[0])
            elif 'Y' in val:
                y = int(val.strip('Y:').split('.')[0])
            elif 'Z' in val:
                z = int(val.strip('Z:').split('.')[0])
            elif 'E' in val:
                break
        return [x, y, z]
        
    def close(self):
        self.ser.close()
        print(bcolors.OKGREEN + "Exiting..." + bcolors.ENDC)

    
    

# Parses model string into list of steps
# (pour type, water weight, flow rate, agitation level (low, medium, high))
def parseSteps(steps):
    parsed = []
    for step in steps.strip('][').split(','):
        temp = step.strip('"').split('/')
        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        parsed.append(temp)
    return parsed


######### Size (inches) ##########
# X117 Y110 - center
# I10 J10 - 1 1/8
# I20 J20 - 2 1/8
# I30 J30 - 3 1/4
# I40 J40 - 4 3/8
######### Times ##################
# 14.56s -  I40 J40 F1500
# 7.43s  -  I20 J20 F1500
# 3.68   -  I20 J20 F3000
# 7.53   -  I40 J40 F3000

# 

# Parses steps into ([gCode], Time) pairs
# Time is when the gcode should be executed
def parseTimes(steps, startTime):
    times_dict = {
        'Center': 1,
        'Inner circle': 3.68,
        'Outer circle': 9, # TODO: Fix estimation thru testing
        'Edge': 16.5, # TODO: Fix estimation thru testing
    }
    gCode = {
        'pre_wet': 'G2 X127 Y115 Z220 I25 J25 F3600', 
        'Center': 'G2 X127 Y115 F3600',
        'Inner circle': 'G2 X127 Y115 I10 J10 F1500',
        'Outer circle': 'G2 X127 Y115 I25 J25 F1500',
        'Edge': 'G2 X127 Y115 I35 J35 F1500',
    }
    
    times = []
    totalTime = startTime
    # TODO: add pump actuation
    # Add in sending gcode signals to printer function
    for step in steps:
        if 'pre_wet' in step:
            step = ([gCode['pre_wet']], totalTime, (2, 10))
            totalTime += timedelta(seconds=10)
        else:
            instructArr = []
            pourTime = step[1] / step[2]  # water weight / flow rate
            numInstruct = math.ceil(pourTime / times_dict[step[0]]) # total time / time per instruction
            step = ([gCode[step[0]]] * numInstruct, totalTime, (step[1], pourTime))
            totalTime += timedelta(seconds=pourTime)
        # Add draw down time
        times.append(step)
        times.append(["Draw down", totalTime])
        totalTime += timedelta(seconds=30)
        
    printTimes(times)
    return times


def printTimes(times):
    i = 0
    for time in times:
        print(f'Step #{i} {time[0]}: {time[1]}')
        i += 1

def printError(error_message):
    print(bcolors.FAIL + '#'*len(error_message))
    print(bcolors.FAIL + error_message)
    print('#'*len(error_message) + bcolors.ENDC)

        
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'