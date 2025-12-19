import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
time.sleep(3)  # Wait for any boot to finish

# Try different line ending combinations
tests = [
    b'AT\r\n',      # Standard
    b'AT\r',        # Just CR
    b'AT\n',        # Just LF  
    b'AT\n\r',      # Reversed
]

for cmd in tests:
    ser.reset_input_buffer()
    print(f"Trying: {repr(cmd)}")
    ser.write(cmd)
    time.sleep(0.5)
    response = ser.read_all()
    print(f"Response: {repr(response)}\n")

ser.close()
