from machine import Pin
from neopixel import NeoPixel

pin = Pin(0, Pin.OUT)   # set GPIO15 to output to drive NeoPixels
np = NeoPixel(pin, 2)   # create NeoPixel driver on GPIO0 for 8 pixels
np[0] = (0, 0, 0)  # set the first pixel to white
np[1] = (0, 0, 0)  # set the second pixel to white
np.write()              # write data to all pixels
r, g, b = np[0]         # get first pixel colour
print(r, g, b)          # prints 255, 255, 255
