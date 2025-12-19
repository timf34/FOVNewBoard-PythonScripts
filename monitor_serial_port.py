import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
print("Listening... Reset the C5 board now (press reset button)")

start = time.time()
while time.time() - start < 10:
    data = ser.read(100)
    if data:
        print(data.decode('utf-8', errors='ignore'), end='')

ser.close()
