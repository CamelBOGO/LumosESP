from machine import Pin, I2C
import time
import asyncio
import gc

# Run the garbage collector to free up memory.
gc.collect()


# ==================================================
# Pin Assignments and Global Variables
# ==================================================
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)


async def shc_measurement():
    # Send wakeup command.
    i2c.writeto(0x70, b"\x35\x17")
    time.sleep(0.001)

    # Send measurement command.
    i2c.writeto(0x70, b"\x7C\xA2")
    await asyncio.sleep(0.001)

    # Read data.
    data = i2c.readfrom(0x70, 6)

    # Send sleep command.
    i2c.writeto(0x70, b"\xB0\x98")
    await asyncio.sleep(0.001)

    # Calculate temperature and humidity.
    temp = data[0] << 8 | data[1]
    humi = data[3] << 8 | data[4]
    temp = -45 + 175 * temp / 65535
    humi = 100 * humi / 65535

    return temp, humi


# ==================================================
# asyncio Functions
# ==================================================
async def temp_handler():
    while True:
        temp, humi = await shc_measurement()
        print(f"Temperature: {temp:0.1f}°C, Humidity: {humi:0.1f}%")

        await asyncio.sleep(1)


# ==================================================
# Main
# ==================================================
# For asyncio, see: https://github.com/orgs/micropython/discussions/10933
# and also see: https://docs.micropython.org/en/latest/library/asyncio.html
async def main():
    task_temp = asyncio.create_task(temp_handler())
    await asyncio.gather(task_temp)

while True:
    asyncio.run(main())
    pass
