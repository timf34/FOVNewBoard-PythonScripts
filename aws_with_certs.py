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

# Reset for clean state
send_cmd('AT+RST', delay=5)
send_cmd('AT')

# Connect WiFi
send_cmd('AT+CWMODE=1')
send_cmd('AT+CWJAP="tim","password"', delay=15)
send_cmd('AT+CIPSTA?', delay=2)

# CRITICAL: Set SNTP time (AWS IoT requires valid time for TLS cert validation)
send_cmd('AT+CIPSNTPCFG=1,0,"pool.ntp.org","time.google.com"', delay=3)
time.sleep(5)  # Wait for time sync
send_cmd('AT+CIPSNTPTIME?', delay=2)

# Configure MQTT for AWS IoT
# Scheme 5 = MQTT over TLS with client certificate (mutual auth)
# cert_key_ID=0, CA_ID=0 (uses the certs flashed into firmware)
send_cmd('AT+MQTTUSERCFG=0,5,"aviva-fov-tablet-1","","",0,0,""', delay=3)

# Set SNI (Server Name Indication) - required for AWS IoT
send_cmd('AT+MQTTSNI=0,"a3lkzcadhi1yzr-ats.iot.eu-west-1.amazonaws.com"', delay=2)

# Connect to AWS IoT (port 8883 for MQTT over TLS)
send_cmd('AT+MQTTCONN=0,"a3lkzcadhi1yzr-ats.iot.eu-west-1.amazonaws.com",8883,1', delay=15)

# If connected, try subscribing to your topic
send_cmd('AT+MQTTSUB=0,"dalymount_IRL/pub",0', delay=3)

# Try publishing a test message
send_cmd('AT+MQTTPUB=0,"dalymount_IRL/pub","test_from_c5",0,0', delay=3)
