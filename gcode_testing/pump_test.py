from gpiozero import DigitalOutputDevice
from time import sleep

output_pin = 25  # GPIO output 25

output_device = DigitalOutputDevice(output_pin)

while True:
        # If input is high, blink output every second
        output_device.on()
        sleep(10)  # 500ms on
        output_device.off()
        sleep(1)  # 500ms off
