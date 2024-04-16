import asyncio
from microdot import Microdot, send_file
import network
# import esp
import gc
from machine import Pin

# Disable vendor OS debug log.
# esp.osdebug(None)
# Run the garbage collector to free up memory.
gc.collect()


# ==================================================
# Pin Assignments
# ==================================================
rPin = Pin(15, Pin.OUT)
gPin = Pin(2, Pin.OUT)
bPin = Pin(4, Pin.OUT)

pinStatesData = {
    "off":  (False, False, False),
    "red":  (True,  False, False),
    "green": (False, True,  False),
    "blue": (False, False, True),
    "default": (True, True, True)
}

ledStatus = "off"


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
wlan.connect(wifiSSID, wifiPassword)

while not wlan.isconnected():
    # try:
    #     # Disconnect and connect again
    #     print(f"Connecting to network...")
    #     wlan.disconnect()
    #     wlan.connect(wifiSSID, wifiPassword)
    #     # Wait for 5 seconds
    # except OSError:
    #     print("Failed to connect to network.")
    pass

# Print the success message and the wlan config.
print("Connection successful")
print(wlan.ifconfig())


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
    ledStatus = data["led"]
    return {"led": ledStatus}, 200


# ==================================================
# Other Functions
# ==================================================
async def led_update():
    global pinStatesData
    while True:
        rState, gState, bState = pinStatesData.get(ledStatus, pinStatesData["default"])
        rPin.value(rState)
        gPin.value(gState)
        bPin.value(bState)
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
