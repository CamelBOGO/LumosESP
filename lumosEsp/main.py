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
# ssid = "ESP32-AP"
# password = "1234567890"


# ==================================================
# Access Point
# https://randomnerdtutorials.com/micropython-esp32-esp8266-access-point-ap/
# ==================================================
# # Create an Access Point.
# ap = network.WLAN(network.AP_IF)
# # Set the AP to be active.
# ap.active(True)
# # Set the AP configuration.
# ap.config(essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=password)

# # While the AP is not active, do nothing.
# while ap.active() == False:
#     pass

# # Print the success message and the ap config.
# print("Connection successful")
# print(ap.ifconfig())


# ==================================================
# Connect to WiFi
# ==================================================
wifiSSID = "TP-LINK_ED469C"
wifiPassword = "Pi3.14159265"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
mac = wlan.config("mac")
host = "esp32-" + "".join("{:02x}".format(b) for b in mac[3:])
wlan.config(dhcp_hostname=host)
wlan.connect(wifiSSID, wifiPassword)

# Wait for the connection to be established
while not wlan.isconnected():
    pass

# Print the success message and the wlan config.
print("Connection successful")
wlan_config = wlan.ifconfig()
host = wlan.config("dhcp_hostname")
print(f'Wifi connected as {host}/{wlan_config[0]}, net={wlan_config[1]}, gw={wlan_config[2]}, dns={wlan_config[3]}')


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
    task_normal = asyncio.create_task(led_update())
    task_server = asyncio.create_task(app.run(port=80, debug=True))
    await asyncio.gather(task_normal, task_server)

while True:
    asyncio.run(main())
    print("ERROR stopped.")
    pass
