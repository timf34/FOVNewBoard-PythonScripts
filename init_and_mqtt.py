import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
time.sleep(2)

def send_cmd(cmd, delay=2):
    ser.write((cmd + '\r\n').encode())
    time.sleep(delay)
    response = ser.read(ser.in_waiting).decode()
    print(f">>> {cmd}")
    print(response)
    print("---")
    return response

# Basic connectivity
send_cmd('AT')
send_cmd('AT+GMR')

# Check available RAM
send_cmd('AT+SYSRAM?')

# List ALL available commands - this will tell us if MQTT is registered
send_cmd('AT+CMD?', delay=5)  # This may take a moment and produce long output

# Try WiFi first (MQTT may need network stack initialized)
send_cmd('AT+CWMODE=1')
send_cmd('AT+CWJAP="tim","password"', delay=10)

# After WiFi connected, try MQTT again
send_cmd('AT+MQTTUSERCFG=?')
