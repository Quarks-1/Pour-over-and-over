import RPi.GPIO as GPIO
import time
# Set up GPIO
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
GPIO.setup(2, GPIO.OUT)   # Set GPIO2 (physical pin 3) as output

try:
    # Turn on GPIO pin
    GPIO.output(2, GPIO.HIGH)
    print("GPIO pin 2 is ON")
    
    # Wait for 5 seconds
    time.sleep(5)
    
    # Turn off GPIO pin
    GPIO.output(2, GPIO.LOW)
    print("GPIO pin 2 is OFF")

finally:
    # Clean up GPIO
    GPIO.cleanup()