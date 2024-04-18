import asyncio
from microdot import Microdot, send_file
import network
import gc
from machine import Pin, PWM

# Run the garbage collector to free up memory.
gc.collect()


# ==================================================
# Pin Assignments and Global Variables
# ==================================================
rPwm = PWM(Pin(15), freq=1000, duty=1023)
gPwm = PWM(Pin(2), freq=1000, duty=1023)
bPwm = PWM(Pin(4), freq=1000, duty=1023)

colourData = {
    "off": 0x000000,
    "red":  0xff0000,
    "green": 0x00ff00,
    "blue": 0x0000ff,
    "default": 0xffffff
}

ledStatus = 0xffffff


# ==================================================
# WiFi and Device Settings
# ==================================================
networkMode = 0  # 0: AP, 1: WiFi, 2: Both
mac = network.WLAN().config("mac")
host = "esp32-" + "".join("{:02x}".format(b) for b in mac[3:])
apSsid = "ESP32-" + "".join("{:02x}".format(b) for b in mac[3:]).upper() + "-AP"
apPassword = "1234567890"
wifiSsid = "TP-LINK_ED469C"
wifiPassword = "Pi3.14159265"
network.hostname(host)


# ==================================================
# General Functions
# ==================================================
# Map a value from one range to another.
def map(value, fromRange, toRange):
    (fromLow, fromHigh) = fromRange
    (toLow, toHigh) = toRange
    return (value - fromLow) * (toHigh - toLow) / (fromHigh - fromLow) + toLow


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
    print("Getting network mode...")
    return {"mode": networkMode, "host": host}, 200


@app.put("/api/wifi")
async def wifi_post(req):
    global wifiSsid, wifiPassword, networkMode

    # Get the json data from the request.
    data = req.json
    print(f"Received data: {data}")

    # Check if the ssid and password are provided.
    if "ssid" in data and "password" in data:
        # Get the ssid and password from the data.
        wifiSsid = data["ssid"]
        wifiPassword = data["password"]
        # Change the network mode to AP/WiFi.
        networkMode = 2
        # Return the network mode and host name.
        return {"mode": networkMode, "host": host}, 200
    else:
        return {"error": "Invalid data"}, 400


@app.get("/api/led")
async def led_get(req):
    print("Getting LED status...")
    return {"led": ledStatus}, 200


@app.put("/api/led")
async def led_put(req):
    global ledStatus

    # Get the json data from the request.
    data = req.json
    print(f"Setting LED to {data["led"]}...")

    # TO-DO: Check if the data is valid.
    # if isinstance(data["led"], int) and 0x000000 <= color <= 0xffffff:
    ledStatus = colourData.get(data["led"], colourData["default"])
    return {"led": ledStatus}, 200


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
        # If the network mode is 0 or 2, activate the AP.
        if networkMode == 0 or networkMode == 2:
            # If the AP is not active, activate the AP. Otherwise, do nothing.
            if ap.active() == False:
                # Activate the AP.
                ap.active(True)
                while ap.active() == False:
                    print("Activating AP...")
                    await asyncio.sleep(1)

                # Print the success message and the ap config.
                print("AP is activated successfully.")
                print(ap.ifconfig())

        # If the network mode is 1, deactivate the AP.
        else:
            # Only deactivate the AP when the AP is active. Otherwise, do nothing.
            if ap.active() == True:
                print("Deactivating AP...")
                ap.active(False)

        await asyncio.sleep(1)


# Function: Connect WiFi
async def wifi_handler():
    # Run the garbage collector to free up memory.
    gc.collect()
    # Create a WLAN object.
    wlan = network.WLAN(network.STA_IF)

    while True:
        # If the network mode is 1 or 2, connect to the WiFi.
        if networkMode == 1 or networkMode == 2:
            # If the wlan is not connected, connect to the WiFi. Otherwise, do nothing.
            if wlan.isconnected() == False:
                # Activate and connect to the WiFi.
                wlan.active(True)
                wlan.connect(wifiSsid, wifiPassword)
                while wlan.isconnected() == False:
                    print("Connecting to WiFi...")
                    await asyncio.sleep(1)

                # Print the success message and the wlan config.
                print("Connection successful")
                wlanConfig = wlan.ifconfig()
                print(
                    f"Wifi connected as {host}/{wlanConfig[0]}, net={wlanConfig[1]}, gw={wlanConfig[2]}, dns={wlanConfig[3]}")

        # If the network mode is 0, deactivate the WiFi.
        else:
            # Only deactivate the WiFi when the WiFi is connected. Otherwise, do nothing.
            if wlan.isconnected() == True:
                print("Disconnecting WiFi...")
                wlan.disconnect()
                wlan.active(False)

        await asyncio.sleep(1)


# Function: Handle the LED colour changing.
async def led_update():
    # Create a local variable to store the current LED status.
    myLedStatus = ledStatus

    while True:
        # If the current LED status is not equal to the target LED status, update the LED status.
        while myLedStatus != ledStatus:
            # Get the target RGB values.
            rTarget = (ledStatus >> 16) & 0xff
            gTarget = (ledStatus >> 8) & 0xff
            bTarget = ledStatus & 0xff

            # Get the current RGB values.
            rCurrent = (myLedStatus >> 16) & 0xff
            gCurrent = (myLedStatus >> 8) & 0xff
            bCurrent = myLedStatus & 0xff

            # Update the current RGB values to the target RGB values by 1 step.
            rCurrent += 0 if rTarget == rCurrent else (1 if rTarget > rCurrent else -1)
            gCurrent += 0 if gTarget == gCurrent else (1 if gTarget > gCurrent else -1)
            bCurrent += 0 if bTarget == bCurrent else (1 if bTarget > bCurrent else -1)

            # Convert the current RGB values to the PWM duty cycle values, and update the duty.
            rPwm.duty(int(map(rCurrent, (0, 255), (0, 1023))))
            gPwm.duty(int(map(gCurrent, (0, 255), (0, 1023))))
            bPwm.duty(int(map(bCurrent, (0, 255), (0, 1023))))

            # Update the current LED status.
            myLedStatus = (rCurrent << 16) | (gCurrent << 8) | bCurrent

            # When the LED colour is changing, use a short delay to make the colour changing smoothly.
            await asyncio.sleep(0.01)

        # If the current LED status is equal to the target LED status, check again in 1 second.
        await asyncio.sleep(1)


# ==================================================
# Main
# ==================================================
# For asyncio, see: https://github.com/orgs/micropython/discussions/10933
# and also see: https://docs.micropython.org/en/latest/library/asyncio.html
async def main():
    task_ap = asyncio.create_task(ap_handler())
    task_wifi = asyncio.create_task(wifi_handler())
    task_led = asyncio.create_task(led_update())
    task_server = asyncio.create_task(app.run(port=80, debug=True))
    await asyncio.gather(task_ap, task_wifi, task_led, task_server)

while True:
    asyncio.run(main())
    print("ERROR stopped.")
    pass
