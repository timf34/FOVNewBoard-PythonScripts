import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
print("Listening... Reset the C5 board now (press reset button)")

# Wait for boot and ready
start = time.time()
buffer = ""
while time.time() - start < 15:
    data = ser.read(100)
    if data:
        text = data.decode('utf-8', errors='ignore')
        print(text, end='')
        buffer += text
        
        # As soon as we see "ready", send AT command
        if "ready" in buffer:
            print("\n\n--- Sending AT command ---")
            time.sleep(0.2)  # Small delay after ready
            ser.write(b'AT\r\n')
            time.sleep(0.5)
            response = ser.read_all()
            print("Response:", response.decode('utf-8', errors='ignore'))
            break

ser.close()
