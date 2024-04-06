from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json, serial, time, math
from datetime import datetime, timedelta

# (pour type, water weight, flow rate, agitation level (low, medium, high))
class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'
    
    profile = None
    printer = None
    arduino = None
    
    x, y, z = 0, 0, 0
    steps = []
    gcodeSteps = []
    startTime = None
    
    def getTime(self):
        return (datetime.now() - self.startTime).total_seconds()

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
            self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 
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
            
            self.profile = BrewProfile.objects.get(id=data['profile'])
            print(f'Profile selected: {self.profile}')
            self.steps = parseSteps(self.profile.steps)
            self.gcodeSteps = parseTimes(self.steps)
            return

        if action == 'startBrew':
            x, y, z = self.printer.currPos()
            print(bcolors.OKBLUE + f'Current position: {x}, {y}, {z}' + bcolors.ENDC)
            self.received_start(data)
            return

        if action == "stopBrew":
            self.received_stop(data)
            return
        
        if action == "restartBrew":
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
        data = self.arduino.readline() 
        decoded_str = data.decode('utf-8')
        while decoded_str == '':
            data = self.arduino.readline() 
            decoded_str = data.decode('utf-8')
        # Strip whitespace and newlines
        clean_str = decoded_str.strip()

        # Split the string based on '/'
        numbers = clean_str.split('/')

        # Convert strings to floats and perform division
        result = (float(numbers[0]), float(numbers[1]))
        data_dict = {
            'weight': result[0],
            'temp': result[1],
        }
        self.broadcast_data(data_dict)


class printer:
    def __init__(self):
        self.center = [127, 115, 0]
        self.ser = serial.Serial("/dev/ttyUSB0", 115200)
        # home printer
        self.ser.write(str.encode("G28 X Y\r\n"))
        # time.sleep(2)
        # TODO: Change Z to proper value
        self.ser.write(str.encode("G0 X117 Y110 Z0 F3600\r\n")) # move to center
    
    def goto(self, x, y, z):
        self.ser.write(str.encode(f"G0 X{x} Y{y} Z{z} F3600\r\n"))
    
    def write(self, command):
        self.ser.write(str.encode(command + "\r\n"))
    
    def arcFromCurr(self, i, j):
        [x, y, z] = self.currPos()
        # Offset from center
        self.ser.write(str.encode(f"G0 X{x-i} Y{y-j} F3600\r\n"))
        # Draw circle
        self.ser.write(str.encode(f"G2 X{x} Y{y} I{i} J{j} F3600\r\n"))
        

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
def parseTimes(steps):
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
    totalTime = 0
    # TODO: add pump actuation
    # Add in sending gcode signals to printer function
    for step in steps:
        if 'pre_wet' in step:
            step = (gCode['pre_wet'], 10)
            continue
        instructArr = []
        pourTime = step[1] / step[2]
        totalTime += pourTime
        numInstruct = math.ceil(times_dict[step[0]] / pourTime)
        step = ([gCode[step[0]]] * numInstruct, totalTime)
        times.append(step)
        
    print(times)
    return times


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