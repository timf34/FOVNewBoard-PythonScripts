import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

print("Waiting for device ready...")
time.sleep(2)

# Clear any pending data
ser.reset_input_buffer()

# Send AT+CMD? to list all commands
print("\n--- Sending AT+CMD? ---")
ser.write(b'AT+CMD?\r\n')
time.sleep(0.5)

# Read response
response = ser.read_all().decode('utf-8', errors='ignore')
print(response)

ser.close()
