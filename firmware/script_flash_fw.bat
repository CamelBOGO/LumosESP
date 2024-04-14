@echo off

echo Running script ...
echo.
set /p PortName=COM?: 

echo %PortName%

@REM echo Installing esptool ......
@REM pip install esptool

@REM echo Installing adafruit-ampy ......
@REM pip install adafruit-ampy

echo Erasing flash ......
esptool --chip esp32 --port %PortName% erase_flash

echo Flashing MicroPython into ESP32 ......
esptool --chip esp32 --port %PortName% --baud 921600 write_flash --flash_size=detect -z 0x1000 ESP32_GENERIC-20240222-v1.22.2.bin

@REM echo Puting main.py to ESP32 ......
@REM ampy --port %PortName% put main.py
@REM echo main.py is running..........

pause