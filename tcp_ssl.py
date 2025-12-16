import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
time.sleep(2)

commands = [
    'AT',
    'AT+GMR',
    'AT+CWMODE=1',
    'AT+CWJAP="tim","password"',
    # Wait for connection...
    'AT+CIPSTART="SSL","a3lkzcadhi1yzr-ats.iot.eu-west-1.amazonaws.com",8443',  # Try port 8443
    'AT+CIPSSLCCONF=?',  # Test if SSL config works
]

for cmd in commands:
    ser.write((cmd + '\r\n').encode())
    time.sleep(3)
    print(f">>> {cmd}")
    print(ser.read(ser.in_waiting).decode())
    print("---")
