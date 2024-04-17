import asyncio
from microdot import Microdot, send_file
import network
# import esp
import gc
from machine import Pin, PWM

# Disable vendor OS debug log.
# esp.osdebug(None)
# Run the garbage collector to free up memory.
gc.collect()


# ==================================================
# Pin Assignments
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
networkMode = 0  # 0: AP, 1: WiFi
mac = network.WLAN().config("mac")
apSsid = "ESP32-AP"
apPassword = "1234567890"
wifiSsid = "wifissid"
wifiPassword = "wifipassword"


# ==================================================
# General Functions
# ==================================================
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
    return {"mode": networkMode}, 200


@app.put("/api/wifi")
async def wifi_post(req):
    global wifiSsid, wifiPassword, networkMode
    data = req.json
    print(f"Received data: {data}")
    # Check if the ssid and password are provided.
    if "ssid" in data and "password" in data:
        wifiSsid = data["ssid"]
        wifiPassword = data["password"]
        networkMode = 1
        return {"mode": networkMode}, 200
    else:
        return {"error": "Invalid data"}, 400


@app.get("/api/led")
async def led_get(req):
    print("Getting LED status...")
    return {"led": ledStatus}, 200


@app.put("/api/led")
async def led_put(req):
    global ledStatus
    data = req.json
    print(f"Setting LED to {data["led"]}...")
    # if isinstance(data["led"], int) and 0x000000 <= color <= 0xffffff:
    ledStatus = colourData.get(data["led"], colourData["default"])
    return {"led": ledStatus}, 200


# ==================================================
# asyncio Functions
# ==================================================
# Access Point
# https://randomnerdtutorials.com/micropython-esp32-esp8266-access-point-ap/
async def ap_setup():
    gc.collect()
    # Create an Access Point.
    ap = network.WLAN(network.AP_IF)
    # Set the AP to be active.
    ap.active(True)
    # Set the AP configuration.
    ap.config(essid=apSsid, authmode=network.AUTH_WPA_WPA2_PSK, password=apPassword)

    while True:
        if networkMode == 1:
            break

        # While the AP is not active, do nothing.
        if ap.active() == False:
            print("Setting up AP...")
            asyncio.sleep(1)
        else:
            # Print the success message and the ap config.
            print("Connection successful")
            print(ap.ifconfig())

            while ap.active():
                if networkMode == 1:
                    break

                await asyncio.sleep(1)

    # If the network mode is changed to WiFi, deactivate the AP.
    print("Deactivating AP...")
    ap.active(False)
    return


async def wifi_connect():
    gc.collect()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    host = "esp32-" + "".join("{:02x}".format(b) for b in mac[3:])
    wlan.config(dhcp_hostname=host)
    wlan.connect(wifiSsid, wifiPassword)

    while True:
        if wlan.isconnected() == False:
            print("Connecting to WiFi...")
            await asyncio.sleep(1)
        else:
            print("Connection successful")
            wlanConfig = wlan.ifconfig()
            host = wlan.config("dhcp_hostname")
            print(
                f"Wifi connected as {host}/{wlanConfig[0]}, net={wlanConfig[1]}, gw={wlanConfig[2]}, dns={wlanConfig[3]}")

            while wlan.isconnected():
                await asyncio.sleep(1)


async def network_control():
    while True:
        if networkMode == 0:
            print("Now entering AP mode...")
            await ap_setup()
        elif networkMode == 1:
            print("Now entering WiFi mode...")
            await wifi_connect()


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
    task_network = asyncio.create_task(network_control())
    task_led = asyncio.create_task(led_update())
    task_server = asyncio.create_task(app.run(port=80, debug=True))
    await asyncio.gather(task_network, task_led, task_server)

while True:
    asyncio.run(main())
    print("ERROR stopped.")
    pass
