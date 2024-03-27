import gpiod
import time
pump_pin = 2
chip = gpiod.Chip('gpiochip4')
pump_line = chip.get_line(pump_pin)
pump_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)
try:
   while True:
       pump_line.set_value(1)
       time.sleep(10)
       pump_line.set_value(0)
       time.sleep(1)
       break
finally:
   pump_line.release()