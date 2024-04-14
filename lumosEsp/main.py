import asyncio
from microdot import Microdot, send_file
import network
import esp
import gc

try:
    import usocket as socket
    print("Using usocket...")
except:
    import socket
    print("Using socket...")

# Disable vendor OS debug log.
esp.osdebug(None)
# Run the garbage collector to free up memory.
gc.collect()

# Create an instance of the Microdot class.
app = Microdot()

# ==================================================
# WiFi and Device Settings
# ==================================================
ssid = "ESP32-AP"
password = "1234567890"


# ==================================================
# Access Point
# https://randomnerdtutorials.com/micropython-esp32-esp8266-access-point-ap/
# ==================================================
# Create an Access Point.
ap = network.WLAN(network.AP_IF)
# Set the AP to be active.
ap.active(True)
# Set the AP configuration.
ap.config(essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=password)

# While the AP is not active, do nothing.
while ap.active() == False:
    pass

# Print the success message and the ap config.
print("Connection successful")
print(ap.ifconfig())


# ==================================================
# The HTML Page
# ==================================================
def web_page():
    html = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Hello, World!</title>
        </head>
        <body>
            <h1>Hello, World!</h1>
        </body>
    </html>
    """
    return html


# ==================================================
# Pages
# ==================================================
# For the symbol of @, see: https://ithelp.ithome.com.tw/articles/10200763
# For async/await, see: https://ithelp.ithome.com.tw/articles/10262385
@app.route("/")
async def hello(request):
    return send_file("./static/index.html", 200)


@app.get("/css/bootstrap.min.css")
async def materialize_css(request):
    return send_file("./static/css/bootstrap.min.css", 200)


@app.get("/js/bootstrap.min.js")
async def materialize_js(request):
    return send_file("./static/js/bootstrap.min.js", 200)

# ==================================================
# APIs
# ==================================================


@app.get("/api/led_on")
async def led_on(request):
    print("LED ON")
    return {"status": "on"}, 200


@app.get("/api/led_off")
async def led_off(request):
    print("LED OFF")
    return {"status": "off"}, 200


# ==================================================
# Other Functions
# ==================================================
async def task():
    while True:
        print("Task running...")
        await asyncio.sleep(3)


# ==================================================
# Main
# ==================================================
# For asyncio, see: https://github.com/orgs/micropython/discussions/10933
# and also see: https://docs.micropython.org/en/latest/library/asyncio.html
async def main():
    task_normal = asyncio.create_task(task())
    task_server = asyncio.create_task(app.run(port=80, debug=True))
    await asyncio.gather(task_normal, task_server)

while True:
    asyncio.run(main())
    print("ERROR stopped.")
    pass
