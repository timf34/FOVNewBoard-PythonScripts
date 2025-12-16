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

# Ensure WiFi is connected first
send_cmd('AT')
send_cmd('AT+CWMODE=1')
send_cmd('AT+CWJAP="tim","password"', delay=10)

# Set SNTP time (required for TLS certificate validation)
send_cmd('AT+CIPSNTPCFG=1,0,"pool.ntp.org"', delay=3)
send_cmd('AT+CIPSNTPTIME?', delay=3)

# Now try MQTT with actual parameters (not =? query)
# Scheme 1 = MQTT over TCP (simplest test)
send_cmd('AT+MQTTUSERCFG=0,1,"esp32c5_test","","",0,0,""', delay=3)

# Check if config was accepted
send_cmd('AT+MQTTCONN?', delay=2)

# Try connecting to a public MQTT broker first (no TLS, no auth)
send_cmd('AT+MQTTCONN=0,"test.mosquitto.org",1883,0', delay=10)
