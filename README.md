# LumosESP

A web server for ESP32 to control the LED lighting.

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
