import serial
import time

print("Connecting to C5...")
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

print("\n⚠️ PRESS THE RESET BUTTON ON THE C5 NOW!")
print("Waiting 3 seconds...")
time.sleep(3)

print("\nSending AT command...")
ser.write(b'AT\r\n')
time.sleep(1)
response = ser.read_all().decode('utf-8', errors='ignore')
print(f"Response: '{response}'")

if response.strip():
    print("✅ C5 is responding!")
else:
    print("❌ No response - C5 might be on wrong UART")

ser.close()
