# LumosESP

A web server for ESP32 to control the LED lighting on MicroPython.

## About

Introducing the latest open-source project from BOGO - a wireless control solution for LED light bases used with acrylic products. Unlike the current market offerings, our project addresses the lack of wireless control options, allowing users to go beyond manual control or single-color modes.

Our solution is a mini web server hosted on an ESP32 microcontroller. Users can connect to this server and control the WS2812 LEDs via a user-friendly web application interface. The project comes pre-loaded with a variety of colour options and modes, including the ability to respond to audio input.

The wireless control capabilities support both Access Point (AP) and Wi-Fi modes, providing users with flexibility in their setup and connectivity options. Additionally, a simple touch control function is supported, providing users with an intuitive way to interact with the lighting setup.

With this open-source project, we aim to empower users to enhance their LED-based acrylic products with wireless control and customization capabilities. Unlock the full potential of your LED light bases and elevate your creative projects to new heights.

## Pin Configuration

From left to right, not including the strapping pins, the pins are as follows:

| Pin    | Function | I/O                      |
| ------ | -------- | ------------------------ |
| GPIO34 | ADC6     | Microphone Input         |
| GPIO15 | TOUCH3   | Touch Spring             |
| GPIO0  | IO0      | Boot                     |
| GPIO4  | GPIO4    | LED Data                 |
| GPIO21 | SDA      | I2C Data (Temp. Sensor)  |
| GPIO22 | SCL      | I2C Clock (Temp. Sensor) |
| GPIO3  | RXD0     | UART RX                  |
| GPIO1  | TXD0     | UART TX                  |

## Used Libraries

-   [MicroPython](https://micropython.org/) by Damien George.
-   [microdot](https://github.com/miguelgrinberg/microdot) by Miguel Grinberg.
-   [Pico CSS](https://picocss.com/) by Adnan Hajdarevic.

## WLED

This project is just a quick implementation of the software part of LumosESP based on MicroPython and SPA concepts. To unlock more features, it is recommended to use the [WLED](https://kno.wled.ge/) library built by Aircoookie and other contributors. However, the WLED has not supported the SHTC3 sensor for temperature and humidity monitoring yet.
