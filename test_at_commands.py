import serial
import time

def send_at_command(ser, command, wait_time=1):
    print(f"\nSending: {command}")
    ser.write((command + '\r\n').encode())
    time.sleep(wait_time)
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(f"Response: {response}")
    return response

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

# Test basic commands
send_at_command(ser, "AT")  # Basic test
send_at_command(ser, "AT+GMR")  # Get version
send_at_command(ser, "AT+CWMODE?")  # Get WiFi mode
send_at_command(ser, "AT+CMD?", 2)  # List available commands
send_at_command(ser, "AT+USERRAM?")
send_at_command(ser, "AT+FWMEMINFO?") 

ser.close()
