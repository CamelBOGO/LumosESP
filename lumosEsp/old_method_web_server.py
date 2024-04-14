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
    html = """<!DOCTYPE html>
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
    
        <body><h1>Hello, World!</h1></body>
    </html>
    """
    return html


# ==================================================
# The Server
# https://jimirobot.tw/esp32-micropython-socket-tcp-server-307-tutorial/
# ==================================================
# Create a new socket using the Internet address family and Stream socket type.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind the socket to address. The address is ("", 80) which means it will bind to all network interfaces of the host on port 80.
s.bind(("", 80))
# Enable the server to accept connections. The argument 5 is the maximum number of queued connections.
s.listen(5)


def parse_request(request):
    # b'GET /?led=on HTTP/1.1\r\nUser-Agent: PostmanRuntime/7.37.0\r\nAccept: */*\r\nPostman-Token: 268426b5-1ddb-4250-a709-8fd304738dd5\r\nHost: 192.168.4.1\r\nAccept-Encoding: gzip, deflate, br\r\nConnection: keep-alive\r\n\r\n'
    lines = request.split('\r\n')
    method, path, version = lines[0].split(' ')
    headers = {}
    for line in lines[1:]:
        if line:
            key, value = line.split(': ', 1)
            headers[key] = value
    return method, path, version, headers


def handle_request(conn):
    # Receive data from the socket, with the maximum amount of data to be received at once is 1024 bytes
    request = conn.recv(1024)
    # Convert the request to a string
    request = str(request)
    # Print the content of the request
    print("Content = %s" % request)

    # Parse the request path
    method, path, version, headers = parse_request(request)
    print(f"\nMethod = {method}")
    print(f"Path = {path}")

    # Handle the path
    if path == "/?led=on":
        print('LED ON')
        response = web_page()
    elif path == "/?led=off":
        print('LED OFF')
        response = web_page()
    elif method == "POST" and path == "/api/led":
        # Parse the body of the POST request
        body = request.split("\r\n\r\n", 1)[1]
        if body == "off":
            print('LED OFF')
        else:
            print('LED ON')
        response = web_page()
    else:
        response = web_page()

    # Send the response
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    # Close the connection
    conn.close()


# ==================================================
# Main
# ==================================================
while True:
    # Accept a connection. The socket must be bound to an address and listening for connections
    conn, addr = s.accept()
    # Print the address of the client that just connected
    print("Got a connection from %s" % str(addr))
    handle_request(conn)
