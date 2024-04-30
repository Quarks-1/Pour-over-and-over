from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json, serial, time, math
from threading import Thread, Timer
from datetime import datetime, timedelta
from simple_pid import PID


# (pour type, water weight, flow rate, agitation level (low, medium, high))
class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'
    
    profile = None
    printer = None
    arduino = None
    
    x, y, z = 0, 0, 0
    steps = []
    queue = []
    startTime = None
    pid = None
    heated = False
    heater = None
    water_temp = 0
    curr_step = 1

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()
        try:
            self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 
        except serial.SerialException:
            printError('WARNING: ARDUINO NOT CONNECTED')
            self.broadcast_message('Arduino not connected. Please connect Arduino and reload page.')
            return
        self.arduino.write(b'pumpon/255\n')
        self.arduino.write(b'heatoff\n')
        
        # Connect to printer
        try:
            self.printer = printer()
        except serial.SerialException:
            printError('WARNING: PRINTER NOT CONNECTED')
            self.broadcast_message('Printer not connected. Please connect printer and reload page.')
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
        # turn off heater
        self.arduino.write(b'pumpon/255\n')
        self.arduino.write(b'heatoff\n')
        

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
            if self.arduino is None or self.printer is None:
                printError('Printer or Arduino not connected')
                return
            # Start PID heating
            # PIDvals
            pid = PID(0.06, 0, 0, setpoint=self.profile.water_temp)  # P=1.0, I=0.1, D=0.05, desired temperature=25°C
            pid.sample_time = 0.5  # Update every 1 second
            pid.output_limits = (0, 1)  # Output value will be between 0 and 1 (off/on)
            self.pid = pid
            # TODO: fix heater start
            self.heater = Thread(target=self.startHeater)
            self.heater.name = f'heater thread'
            return

        if action == 'startBrew':
            if not self.heated and self.profile.water_temp > self.water_temp:
                self.broadcast_message('Water not yet heated. Please wait...')
                printError('Water not heated')
                return
            print('Starting brew...')
            self.broadcast_message('Starting brew...')
            self.schedulePours(self.steps)
            return

        if action == "stopBrew":
            self.broadcast_message('Brew stopped.')
            print('Stopping brew...')
            for timer in self.queue:
                timer.cancel()
            self.arduino.write(b'pumpon/255\n')
            self.arduino.write(b'heatoff\n')
            self.queue = []
            return
        
        if action == "restartBrew":
            self.broadcast_message('Brew restarted.')
            self.broadcast_message('enable all buttons')
            # parse steps again
            self.steps = parseSteps(self.profile.steps)
            for timer in self.queue:
                timer.cancel()
            self.queue = []
            self.schedulePours(self.steps)
            self.curr_step = 1
            return
        
        if action == 'tareScale':
            self.arduino.write(b'tare\n')
            self.broadcast_message('Scale tared.')
            return
        
        if action == 'updateData':
            thread = Thread(target=self.get_arduino_feed)
            thread.start()
            return

        if action == 'bypassTemp':
            self.broadcast_message('Bypassing temperature check...')
            self.broadcast_message('disable bypass button')
            self.arduino.write(b'heatoff\n')
            self.heated = True
            return

        if action == 'startHeater':
            self.broadcast_message('Heating water. Please wait...')
            self.heater.start()
            self.broadcast_message('disable heater button')
            return

        printError(f'Invalid action property: "{action}"')

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
    
    previous_data = None
    def get_arduino_feed(self):
        # self.arduino.reset_input_buffer()
        time.sleep(0.1)
        data = self.arduino.readline() 

        # Decode byte string to a normal string
        decoded_str = data.decode('utf-8')
        parts = decoded_str.strip().split('/')
        if self.previous_data is not None and decoded_str == '' or len(parts) != 2 or len(parts[0]) < 3 or len(parts[1]) < 2:
            self.broadcast_data(self.previous_data)
            return        
        current_data = (parts[0], parts[1])

        result = (float(current_data[0]), float(current_data[1]))
        self.water_temp = result[1]
        data_dict = {
            'weight': result[0],
            'temp': result[1],
        }
        self.previous_data = data_dict
        self.broadcast_data(data_dict)
        return result
    
    # TODO: Test heating
    # Turn on water heater
    def startHeater(self):
        self.broadcast_message('Heating water. Please wait...')
        while not self.heated:
            try:
                # Read temperature from serial
                data = self.get_arduino_feed()
                if data:
                    current_temp = float(data[1])
                    # print(f"Current Temperature: {current_temp}°F")
                    control = self.pid(current_temp)
                    heating_on = control >= 0.5 
                    print(f'PID control: {control}, heating on: {heating_on}, current temp: {current_temp}°F')
                    self.arduino.write(b'heaton\n' if heating_on else b'heatoff\n')
                    if current_temp >= self.profile.water_temp:
                        self.broadcast_message('Water heated. Click to start brew...')
                        break
                time.sleep(0.01)
            except ValueError:
                # In case of faulty serial data that cannot be converted to float
                print("Invalid data received.")
            except serial.SerialException:
                printError('Arduino error')
            time.sleep(0.01)
        self.heated = True
        self.arduino.write(b'heatoff\n')
        return
        

    def schedulePours(self, steps):
        print('Scheduling pours...')
        # TODO: fine tune step times
        times_dict = {
            'Center': 1,
            'Inner circle': 4,
            'Outer circle': 9,
            'Edge': 13, 
        }
        gCode = {
            'pre_wet': 'G2 X127 Y115 Z220 I25 J25 F3600', 
            'Center': 'G2 X127 Y115 F3600',
            'Inner circle': 'G2 X127 Y115 I10 J10 F1500',
            'Outer circle': 'G2 X127 Y115 I25 J25 F1500',
            'Edge': 'G2 X127 Y115 I35 J35 F1500',
        }
        startTime = datetime.now()
        totalTime = datetime.now() + timedelta(seconds=2)
        # print(steps)
        for step in steps:
            if 'pre_wet' in step:
                finalStep = ([gCode['pre_wet']], [20, 2])
                stepTime = timedelta(seconds=5)
            elif 'delay' in step:
                draw_down_message = 'Draw down'
                stepTime = timedelta(seconds=step[1])
                timer = Timer((totalTime - startTime).total_seconds(), self.broadcast_message, args=([draw_down_message]))
                self.queue.append(timer)
                timer.start() 
            else:
                pourTime = step[1] / step[2] + 1  # water weight / flow rate
                numInstruct = math.ceil(pourTime / times_dict[step[0]]) # total time / time per instruction
                # print(f'number of instructions: {numInstruct}')
                finalStep = ([gCode[step[0]]] * numInstruct, [step[1], step[2]])
                # print(f'taking max of {pourTime} and {times_dict[step[0]]} * {numInstruct}')
                stepTime = timedelta(seconds=max(pourTime, times_dict[step[0]] * numInstruct))
                # print(f'Pouring {step[1]}g at {step[2]}g/s for {stepTime.total_seconds()} seconds')
            if 'delay' not in step:
                strstep = [list2str(finalStep[0]), list2str(finalStep[1])]
                timer = Timer((totalTime - startTime).total_seconds(), self.doStep, args=(strstep))
                timer.name = f'thread for: {step}'
                self.queue.append(timer)
                timer.start()
            totalTime += stepTime
        finished_message = 'Finished brewing, Enjoy!'
        # Send finished message
        timer = Timer((totalTime - startTime).total_seconds(), self.broadcast_message, args=([finished_message]))
        self.queue.append(timer)
        timer.start()   
        # print(self.queue)    
         
    def doStep(self, gcode, water):
        # highlight step on web page
        self.broadcast_message(f'curr step:{self.curr_step}')
        self.curr_step += 1
        
        gcode = str2list(gcode)
        water = str2list(water)
        water[0] = float(water[0])
        water[1] = float(water[1])
        print(f'doStep: Pouring {water[0]}g at {water[1]}g/s')
        # Actuate pump
        pour = Thread(target=self.doPour, args=(water))
        pour.name = f'Pouring {water[0]}g at {water[1]}g/s'
        pour.start()
        time.sleep(1.66)
        # Send gcode to printer
        for command in gcode:
            # Check if command is circle
            if 'I' in command:
                [i, j, x, y] = [int(command.split('I')[1].split(' ')[0]), int(command.split('J')[1].split(' ')[0]), int(command.split('X')[1].split(' ')[0]), int(command.split('Y')[1].split(' ')[0])]
                self.printer.arcFromCurr(i, j, x, y)
            else:
                self.printer.write(command)
            time.sleep(0.05)
        
    
    def doPour(self, water_weight, flowRate):
        # Prime
        self.arduino.write(b'pumpon/255\n')
        time.sleep(10)
        # Send signal to arduino
        print(f'Pouring {water_weight}g at {flowRate}g/s, value: {self.map_value(flowRate)}')
        message = f'pumpon/{self.map_value(flowRate)}\n'
        # message = f'pumpon/{255}\n'
        self.arduino.write(message.encode())
        time.sleep(water_weight/flowRate)
        # print(f'Pouring for {water_weight/flowRate} seconds')
        self.arduino.write(b'pumpon/255\n')
        return
    
    def map_value(x):
        if x == 0:
            return 255
        elif 1 <= x <= 8:
            return -10 * x + 80
        else:
            raise ValueError("Input should be between 0 and 8")



class printer:
    def __init__(self):
        self.center = [127, 115, 0]
        self.ser = serial.Serial("/dev/ttyUSB0", 115200)
        # home printer
        self.ser.write("G28 X Y\r\n".encode())
        # TODO: Change Z to proper value
        self.ser.write("G0 X117 Y110 Z220 F3600\r\n".encode()) # move to center
        self.ser.write("M106 S255\r\n".encode())
        self.ser.write("M106 P1 S255\r\n".encode())
        time.sleep(10)
    
    def goto(self, x, y, z):
        command = f"G0 X{x} Y{y} Z{z} F3600\r\n"
        self.ser.write(command.encode())
    
    def write(self, command):
        self.ser.write(str.encode(command + "\r\n"))
    
    def arcFromCurr(self, i, j, x, y):
        # Offset from center
        # print(f'Current position: {x}, {y}, i: {i}, j: {j}')
        command = f"G0 X{x-i} Y{y-j} F3600\r\n"
        self.ser.write(command.encode())
        time.sleep(0.1)
        # Draw circle
        command = f"G2 X{x-i} Y{y-j} I{i} J{j} F1500\r\n"
        self.ser.write(command.encode())
        time.sleep(0.1)
        

    def currPos(self) -> list[int, int, int]:
        self.ser.reset_input_buffer()
        self.ser.write("M114\r\n".encode())
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
        # print(f'parsing: {step}')
        temp = step.strip("'").split('/')
        if ' ' in temp[0]:
            temp[0] = temp[0][2:]
        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        parsed.append(temp)
        # print(f'parsed: {temp}')
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


def list2str(L) -> str:
    return ', '.join([str(elem) for elem in L])

def str2list(string) -> list:
    return [elem for elem in string.split(', ')]

def printTimes(times):
    i = 0
    for time in times:
        print(f'Step #{i} {time[0]}: {time[1]}')
        i += 1

def printError(error_message):
    print(bcolors.FAIL + '#'*len(error_message) + error_message + '#'*len(error_message) + bcolors.ENDC)

        
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
    
    
# Useful links
# https://stackoverflow.com/questions/11523918/start-a-function-at-given-time