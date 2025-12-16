import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

# Send AT command
ser.write(b'AT\r\n')
time.sleep(0.5)
response = ser.read_all()
print("Response:", response.decode('utf-8', errors='ignore'))

ser.close()
