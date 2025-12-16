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

# Reset and connect fresh
send_cmd('AT+RST', delay=3)
send_cmd('AT')
send_cmd('AT+CWMODE=1')

# Connect to WiFi and WAIT for stable connection
send_cmd('AT+CWJAP="tim","password"', delay=15)  # Longer wait

# Verify we have IP
send_cmd('AT+CIPSTA?', delay=2)

# Test DNS is working
send_cmd('AT+CIPDOMAIN="test.mosquitto.org"', delay=5)

# If DNS works, configure MQTT
send_cmd('AT+MQTTUSERCFG=0,1,"esp32c5_fov","","",0,0,""', delay=2)

# Connect to public broker
send_cmd('AT+MQTTCONN=0,"test.mosquitto.org",1883,0', delay=10)

# If connected, try subscribe and publish
send_cmd('AT+MQTTSUB=0,"fov/test",0', delay=3)
send_cmd('AT+MQTTPUB=0,"fov/test","hello_from_c5",0,0', delay=3)

# Clean up
send_cmd('AT+MQTTCLEAN=0', delay=2)
