import gpiod
import time

from gpiod.line import Direction, Value

LINE = 13

with gpiod.request_lines(
    "/dev/gpiochip0",
    consumer="blink-example",
    config={
        LINE: gpiod.LineSettings(
            direction=Direction.OUTPUT, output_value=Value.ACTIVE
        )
    },
) as request:
    while True:
        request.set_value(LINE, Value.ACTIVE)
        time.sleep(10)
        request.set_value(LINE, Value.INACTIVE)
        time.sleep(1)