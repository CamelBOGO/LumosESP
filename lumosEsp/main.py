from neopixel import NeoPixel
from machine import Pin, TouchPad, ADC
from microdot import Microdot, send_file
import asyncio
import network
import gc

# Run the garbage collector to free up memory.
gc.collect()
# ==================================================
# WiFi and Device Settings
# ==================================================
networkMode = 1  # 0: AP, 1: WiFi, 2: Both
mac = network.WLAN().config("mac")
host = "esp32-" + "".join("{:02x}".format(b) for b in mac[3:])
apSsid = "ESP32-" + "".join("{:02x}".format(b) for b in mac[3:]).upper() + "-AP"
apPassword = "1234567890"
wifiSsid = "TP-LINK_ED469C"
wifiPassword = "Pi3.14159265"
network.hostname(host)
gc.collect()


# ==================================================
# Pin Assignments and Global Variables
# ==================================================
# Touch Pad
touchPin = TouchPad(Pin(15))

# ADC for MIC
mic = ADC(Pin(34), atten=ADC.ATTN_11DB)
micValueMax = 0  # The global variable to store the amplitude. It will be reduced slowly.
inAudioMode = True  # Set to True to enable the audio mode.

# NeoPixel
numOfLeds = 5
ledPin = Pin(4, Pin.OUT)
neoPixels = NeoPixel(ledPin, numOfLeds)

# Initialise all neopixels to white.
for i in range(numOfLeds):
    neoPixels[i] = (255, 255, 255)
neoPixels.write()

# Initial LED Status
ledTargetRgb = 0xffffff
ledStatusList = [0xffffff, 0xff0000, 0xffff00, 0x00ff00, 0x00ffff, 0x0000ff, 0xff00ff, "cycle", "rainbow"]


# ==================================================
# General Functions
# ==================================================
# Convert a hex colour to RGB.
def hex_to_rgb(value):
    # Check if the input is an integer.
    if not isinstance(value, int):
        raise TypeError('Input must be an integer')
    # Check if the input is in the valid range.
    value = value & 0xffffff
    # Convert and return the RGB colour.
    r = (value >> 16) & 0xff
    g = (value >> 8) & 0xff
    b = value & 0xff
    return r, g, b


# Convert RGB to a hex colour.
def rgb_to_hex(r, g, b):
    # Check if the inputs are integers.
    if not all(isinstance(i, int) for i in (r, g, b)):
        raise TypeError("Inputs must be integers")
    # Check if the inputs are in the valid range.
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    # Convert and return the hex colour.
    return (r << 16) | (g << 8) | b


# Convert HSV to RGB.
# Input: h, s, v where h is in the range 0-360, s and v are in the range 0-1.
# Output: (r, g, b) where r, g, b are integers in the range 0-255.
def hsv_to_rgb(h, s, v):
    # Check if the inputs are in the valid range.
    if not (0 <= h <= 360 and 0 <= s <= 1 and 0 <= v <= 1):
        # If hue is out of range, rotate it back in range.
        h = h % 360
        # Fix the inputs to the valid range.
        s = max(0, min(s, 1))
        v = max(0, min(v, 1))

    # Convert and return the RGB colour.
    h = h / 60
    i = int(h)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    r, g, b = {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q)
    }[i % 6]

    # Convert the RGB values to the integer format.
    return int(r * 255), int(g * 255), int(b * 255)


# Convert RGB to HSV.
# Input: r, g, b where r, g, b are integers in the range 0-255.
# Output: (h, s, v) where h is in the range 0-360, s and v are in the range 0-1.
def rgb_to_hsv(r, g, b):
    # Check if the inputs are integers.
    if not all(isinstance(i, int) for i in (r, g, b)):
        raise TypeError("Inputs must be integers")

    # Check if the inputs are in the valid range.
    if not all(0 <= i <= 255 for i in (r, g, b)):
        # Fix the inputs to the valid range.
        r = max(0, min(r, 255))
        g = max(0, min(g, 255))
        b = max(0, min(b, 255))

    # Convert and return the HSV colour.
    r, g, b = r / 255, g / 255, b / 255
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin

    if delta == 0:
        h = 0
    elif cmax == r:
        h = 60 * (((g - b) / delta) % 6)
    elif cmax == g:
        h = 60 * (((b - r) / delta) + 2)
    elif cmax == b:
        h = 60 * (((r - g) / delta) + 4)

    if cmax == 0:
        s = 0
    else:
        s = delta / cmax

    v = cmax

    return h, s, v


# ==================================================
# Pages
# ==================================================
# For the symbol of @, see: https://ithelp.ithome.com.tw/articles/10200763
# For async/await, see: https://ithelp.ithome.com.tw/articles/10262385
# Create an instance of the Microdot class.
app = Microdot()


@app.route("/")
async def send_index(req):
    return send_file("./static/index.html", 200)


@app.get("/css/pico.indigo.min.css")
async def send_css(req):
    return send_file("./static/css/pico.indigo.min.css", 200)


# ==================================================
# APIs
# ==================================================
@app.get("/api/wifi")
async def wifi_get(req):
    return {
        "mode": networkMode,
        "host": host,
        # Only return the IP address when the network mode is not AP.
        "ip": network.WLAN().ifconfig()[0] if networkMode != 0 else None
    }, 200


@app.put("/api/wifi")
async def wifi_post(req):
    global wifiSsid, wifiPassword, networkMode

    # Get the json data from the request.
    data = req.json

    # Check if the ssid and password are provided.
    if "ssid" in data and "password" in data:
        # Get the ssid and password from the data.
        wifiSsid = data["ssid"]
        wifiPassword = data["password"]
        # Change the network mode to AP/WiFi.
        networkMode = 2
        # Return the network mode and host name.
        return {"mode": networkMode, "host": host, "ip": network.WLAN().ifconfig()[0]}, 200
    else:
        return {"error": "Invalid data"}, 400


@app.put("/api/network_mode")
async def network_mode_put(req):
    global networkMode

    # Get the json data from the request.
    data = req.json

    # Check if the mode is provided and valid.
    if "mode" in data and data["mode"] in [0, 1, 2]:
        networkMode = data["mode"]
        return {"mode": networkMode}, 200
    else:
        return {"error": "Invalid data"}, 400


@app.get("/api/led")
async def led_get(req):
    return {"led": ledTargetRgb}, 200


@app.put("/api/led")
async def led_put(req):
    global ledTargetRgb

    # Get the json data from the request.
    data = req.json

    # Check if the data is existed and valid.
    if "led" in data and isinstance(data["led"], int) and 0 <= data["led"] <= 0xffffff:
        ledTargetRgb = data["led"]
        return {"led": ledTargetRgb}, 200
    elif "led" in data and (data["led"] in ["cycle", "rainbow"]):
        # Currently, there is no specific handling for the "cycle" status.
        ledTargetRgb = data["led"]
        return {"led": ledTargetRgb}, 200
    else:
        return {"error": "Invalid data"}, 400


@app.get("/api/audio_mode")
async def audio_mode_get(req):
    return {"isAudio": inAudioMode}, 200


@app.put("/api/audio_mode")
async def audio_mode_put(req):
    global inAudioMode

    # Get the json data from the request.
    data = req.json

    # Check if the data is existed and valid.
    if "isAudio" in data and isinstance(data["isAudio"], bool):
        inAudioMode = data["isAudio"]
        return {"isAudio": inAudioMode}, 200
    else:
        return {"error": "Invalid data"}, 400


# ==================================================
# asyncio Functions
# ==================================================
# Function: Access Point
# https://randomnerdtutorials.com/micropython-esp32-esp8266-access-point-ap/
async def ap_handler():
    # Run the garbage collector to free up memory.
    gc.collect()
    # Setting of the AP object.
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=apSsid, authmode=network.AUTH_WPA_WPA2_PSK, password=apPassword)

    while True:
        # If the network mode is 0 or 2, and the AP is not activated, activate the AP.
        if networkMode in [0, 2] and not ap.active():
            # Activate the AP.
            ap.active(True)
            while not ap.active():
                await asyncio.sleep(1)

            # Print the success message and the ap config.
            # print("AP is activated successfully.")
            # print(ap.ifconfig())

        # If the network mode is 1, and the AP is activated, deactivate the AP.
        elif networkMode == 1 and ap.active():
            ap.active(False)

        await asyncio.sleep(2)


# Function: Connect WiFi
async def wifi_handler():
    # Global variables
    global networkMode, host, wifiSsid, wifiPassword
    # Run the garbage collector to free up memory.
    gc.collect()
    # Create a WLAN object and setting.
    wlan = network.WLAN(network.STA_IF)

    while True:
        # If the network mode is 1 or 2, and the WiFi is not connected, connect to the WiFi.
        if networkMode in [1, 2] and not wlan.isconnected():
            # Activate and connect to the WiFi.
            wlan.active(True)
            wlan.config(dhcp_hostname=host)
            wlan.connect(wifiSsid, wifiPassword)

            # The loop to wait for the WiFi connection.
            attempts = 0
            while not wlan.isconnected():
                # Only try 10 times to connect to the WiFi.
                if attempts >= 10:
                    # print("Connection failed. Switching to AP mode...")
                    networkMode = 0
                    break
                attempts += 1
                await asyncio.sleep(2)

            # Print the success message and the wlan config.
            if wlan.isconnected():
                print("Connection successful")
                wlanConfig = wlan.ifconfig()
                print(
                    f"Wifi connected as {host}/{wlanConfig[0]}, net={wlanConfig[1]}, gw={wlanConfig[2]}, dns={wlanConfig[3]}")

        # If the network mode is 0, and the WiFi is connected, disconnect the WiFi.
        elif networkMode == 0 and wlan.isconnected():
            wlan.disconnect()
            wlan.active(False)

        await asyncio.sleep(2)


# Function: Turn off all LEDs smoothly and no matter what colour they are.
async def led_off():
    done_flag = False
    step = 2
    while done_flag == False:
        done_flag = True
        # Scan through all the LEDs and reduce the RGB values by 1.
        for i in range(numOfLeds):
            # Get the current RGB values.
            r, g, b = neoPixels[i]

            # Update the RGB values by 1 step.
            r = max(r - step, 0)
            g = max(g - step, 0)
            b = max(b - step, 0)

            # Update the done flag.
            done_flag = False if any([r, g, b]) else True

            # Update the NeoPixel colour.
            neoPixels[i] = (r, g, b)

        neoPixels.write()
        await asyncio.sleep(0.01)


# Function: Handle the LED single colour mode.
async def led_single():
    global ledTargetRgb, inAudioMode, micValueMax

    # Get the current LED status.
    myLedStatusRgb = rgb_to_hex(*neoPixels[0])

    # Initialize the HSV values.
    hCurrent, sCurrent, vCurrent = None, None, None

    # Check if the current LED status is off.
    if myLedStatusRgb == 0:
        # If yes, use the target LED status, and set the brightness to 0.
        hCurrent, sCurrent, vCurrent = rgb_to_hsv(*hex_to_rgb(ledTargetRgb))
        vCurrent = 0
    else:
        hCurrent, sCurrent, vCurrent = rgb_to_hsv(*hex_to_rgb(myLedStatusRgb))

    # If it is still in single colour mode, update the target HSV values.
    while isinstance(ledTargetRgb, int) and ledTargetRgb != 0:  # int means still in single colour, 0 means off
        # Update the target HSV values to prevent the LED status from changing during the audio mode.
        hTarget, sTarget, vTarget = rgb_to_hsv(*hex_to_rgb(ledTargetRgb))

        # If in audio mode, use the value from the mic_handler.
        if inAudioMode:
            vTarget = micValueMax / 65535
            vCurrent = vTarget

        # Update the current HSV values to the target HSV values by 1 or 0.01 step.
        # If the difference is less than the step, set the current value to the target value directly.
        # Otherwise, increase or decrease the current value to get closer to the target value.
        hCurrent = hTarget if abs(hTarget - hCurrent) < 1 \
            else (hCurrent + 1 if hTarget > hCurrent else hCurrent - 1)
        sCurrent = sTarget if abs(sTarget - sCurrent) < 0.015 \
            else (sCurrent + 0.01 if sTarget > sCurrent else sCurrent - 0.01)
        vCurrent = vTarget if abs(vTarget - vCurrent) < 0.015 \
            else (vCurrent + 0.01 if vTarget > vCurrent else vCurrent - 0.01)

        # Update and write the NeoPixel colour.
        for i in range(numOfLeds):
            rgb = hsv_to_rgb(hCurrent, sCurrent, vCurrent)
            neoPixels[i] = rgb
        neoPixels.write()

        # When the LED colour is changing, use a short delay to make the colour changing smoothly.
        await asyncio.sleep(0.01)


# Function: Handle the LED colour cycling. Handle in HSV format.
async def led_colour_cycle():
    # Get the current RGB values.
    rCurrent, gCurrent, bCurrent = neoPixels[0]
    h, s, v = rgb_to_hsv(rCurrent, gCurrent, bCurrent)

    while ledTargetRgb == "cycle":
        # Do the colour cycling.
        h = (h + 1) % 360
        s = min(s + 0.01, 1)
        v = min(v + 0.01, 1)

        # Convert the HSV values back to RGB values.
        rCurrent, gCurrent, bCurrent = hsv_to_rgb(h, s, v)

        # Update the NeoPixel colour.
        for i in range(numOfLeds):
            neoPixels[i] = (rCurrent, gCurrent, bCurrent)

        # Write the NeoPixel data.
        neoPixels.write()

        # When the LED colour is cycling, use a short delay to make the colour cycling smoothly.
        await asyncio.sleep(0.01)


# Function: Handle the LED rainbow effect.
async def led_rainbow():
    val = 0.01
    while ledTargetRgb == "rainbow":
        # Loop through the hue values (0 to 360).
        for hue in range(0, 360, 1):
            # If the LED status is not "rainbow", break the loop.
            if ledTargetRgb != "rainbow":
                return

            # Update the NeoPixel colour.
            for ledNum in range(numOfLeds):
                # Add the hue value to different LEDs, the added value is based on the LED number: hue + 360*(ledNum/numOfLeds)
                neoPixels[ledNum] = hsv_to_rgb(hue + (360 * ledNum / numOfLeds), 1, val)
            neoPixels.write()

            # Assume the LEDs are off, increment val for brightness, but do not exceed 1.
            if val < 1:
                val = min(val + 0.01, int(1))

            await asyncio.sleep(0.01)


# Function: Handle the LED colour changing.
async def led_handler():
    global ledTargetRgb, inAudioMode, micValueMax

    while True:
        # If the target LED status is "cycle" or "rainbow", start the LED cycling.
        if ledTargetRgb == "cycle":
            await led_colour_cycle()
            continue
        elif ledTargetRgb == "rainbow":
            await led_off()
            await led_rainbow()
            await led_off()
            continue
        elif isinstance(ledTargetRgb, int) and ledTargetRgb == 0:
            await led_off()
            continue
        else:
            await led_single()
            continue

        await asyncio.sleep(0.1)


# Function: Touch Handler
async def touch_handler():
    global ledTargetRgb
    isTouched = False
    touchThreshold = 350
    while True:
        # Get the touch value.
        touchValue = touchPin.read()

        if touchValue <= touchThreshold and not isTouched:
            # Change the LED status to the next one.
            ledTargetRgb = ledStatusList[(ledStatusList.index(ledTargetRgb) + 1) % len(ledStatusList)]

            # print(f"Touch changed LED to: {ledTargetRgb}.")
            isTouched = True
        elif touchValue > touchThreshold and isTouched:
            isTouched = False

        # Wait for 0.5 second before checking the touch value again.
        await asyncio.sleep(0.2)


# Function: ADC for MIC
async def mic_handler():
    global micValueMax
    dymamic_range = 3000  # Initialize with a small value
    decay_rate = 0.995  # Adjust this value to change the rate of decay
    while True:
        if inAudioMode:
            # Get 32 sound samples
            samples = []
            for i in range(32):
                samples.append(mic.read_u16())

            # Calculate the amplitude.
            micValue = max(samples) - min(samples)
            # print(f"MIC: {micValue}")

            # Update the dynamic range if necessary
            if micValue > dymamic_range:
                dymamic_range = micValue
            # Else, reduce the dynamic range slowly.
            else:
                dymamic_range = max(int(dymamic_range - 1), 3000)

            # Remap the value according to the dynamic range
            micValue = int((micValue / dymamic_range) * 65535)

            # Update the MIC value to the global variable.
            if micValue > micValueMax:
                micValueMax = micValue
            # Else, reduce the MIC value slowly.
            else:
                micValueMax = max(int(micValueMax * decay_rate), 0)

            # Print the MIC value
            # print(f"MIC Max: {micValueMax}")

        await asyncio.sleep(0.001)


# ==================================================
# Main
# ==================================================
# For asyncio, see: https://github.com/orgs/micropython/discussions/10933
# and also see: https://docs.micropython.org/en/latest/library/asyncio.html
async def main():
    task_ap = asyncio.create_task(ap_handler())
    task_wifi = asyncio.create_task(wifi_handler())
    task_led = asyncio.create_task(led_handler())
    task_touch = asyncio.create_task(touch_handler())
    task_mic = asyncio.create_task(mic_handler())
    task_server = asyncio.create_task(app.run(port=80, debug=True))
    await asyncio.gather(task_ap, task_wifi, task_led, task_touch, task_mic, task_server)

while True:
    asyncio.run(main())
    pass
