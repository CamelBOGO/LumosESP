from machine import TouchPad, Pin
import time

# LED Pin
led = Pin(4, Pin.OUT)
led.value(0)

while True:
    t = TouchPad(Pin(15))
    t.read()              # Returns a smaller number when touched

    if t.read() < 200:
        led.value(1)
    else:
        led.value(0)

    # time.sleep(0.01)
