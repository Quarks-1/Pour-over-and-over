from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json, serial, time

class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'
    
    profile = None
    printer = None
    x, y, z = 0, 0, 0
    steps = []

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
            self.broadcast_error('Printer not connected. Please connect printer and reload page.')
            return
        self.broadcast_data()

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
        print(data)
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
            steps = parseSteps(self.profile.steps)
            self.broadcast_data()
            return

        if action == 'startBrew':
            x, y, z = self.printer.currPos()
            self.received_start(data)
            return

        if action == "stopBrew":
            self.received_stop(data)
            return
        
        if action == "restartBrew":
            self.received_restart(data)
            return

############# Is there a need for pausing??? ################
        if action == 'pauseBrew':
            self.received_pause(data)
            return

        if action == 'resumeBrew':
            self.received_resume(data)
            return

#############################################################
        
        printError(f'Invalid action property: "{action}"')

################## To be filled in #######################
    def received_start(self, data):
        
        self.broadcast_data()
    
    def received_pause(self, data):
        self.broadcast_data()
    
    def received_resume(self, data):
        self.broadcast_data()
        
    def received_stop(self, data):
        self.broadcast_data()
        
    def received_restart(self, data):
        self.broadcast_data()
################################################

    def broadcast_data(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': ""
            }
        )
    
    def broadcast_error(self, error_message):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(error_message)
            }
        )
    def broadcast_event(self, event):
        self.send(text_data=event['message'])


class printer:
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyUSB0", 115200)
        self.ser.write(str.encode("G91\r\n")) # set to relative positioning
        self.ser.write(str.encode("G92 Z200\r\n")) # offset to not hit top
        self.ser.write(str.encode('G0 Z150 F3600\r\n')) # move down
        self.ser.write(str.encode("G90\r\n")) # set to absolute positioning
        self.ser.write(str.encode("G28 X Y Z\r\n")) # home printer
        self.ser.write(str.encode("G0 X127 Y90 Z220 F3600\r\n")) # move to center
    
    def write(self, command):
        self.ser.write(str.encode(command + "\r\n"))

    def currPos(self) -> list[int, int, int]:
        self.ser.write(str.encode("M114\r\n"))
        time.sleep(2)
        self.ser.readline()
        x, y, z = 0, 0, 0
        for val in self.ser.readline().split(' '):
            if 'X' in val:
                x = int(val.strip('X:'))
            elif 'Y' in val:
                y = int(val.strip('Y:'))
            elif 'Z' in val:
                z = int(val.strip('Z:'))
            elif 'E' in val:
                break
        return [x, y, z]
        
    def close(self):
        self.ser.close()
        print(bcolors.OKGREEN + "Exiting..." + bcolors.ENDC)

# (pour type, water weight, flow rate, agitation level (low, medium, high))
def parseSteps(steps):
    parsed = []
    for step in steps.strip('][').split(','):
        temp = step.strip('"').split('/')
        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        parsed.append(temp)
    print(parsed)
    return parsed
    

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