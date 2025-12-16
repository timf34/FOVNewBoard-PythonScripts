import serial
import time

def send_command(ser, cmd):
    """Send AT command and print response"""
    print(f"\n{'='*50}")
    print(f"Sending: {cmd}")
    print('='*50)
    ser.write((cmd + '\r\n').encode())
    time.sleep(1)
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(f"Response:\n{response}")
    
    # Check result
    if "ERROR" in response and cmd.endswith("?"):
        print("❌ FAILED - Command not supported")
        return False
    elif response.strip():
        print("✅ Got response")
        return True
    else:
        print("⚠️ No response")
        return None

# Connect to C5
print("Connecting to C5...")
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

# Test basic command
send_command(ser, "AT")

# Test firmware version
send_command(ser, "AT+GMR")

print("\n" + "="*50)
print("CRITICAL TEST: MQTT Commands")
print("="*50)

# THE KEY TEST - If this works, MQTT is enabled!
mqtt_works = send_command(ser, "AT+MQTTUSERCFG=?")

# Test more MQTT commands
send_command(ser, "AT+MQTTCONN=?")
send_command(ser, "AT+MQTTSUB=?")
send_command(ser, "AT+MQTTPUB=?")

# Test SSL
print("\n" + "="*50)
print("SSL/TLS Support")
print("="*50)
send_command(ser, "AT+CIPSSLCCONF=?")

# Summary
print("\n" + "="*50)
print("RESULT")
print("="*50)
if mqtt_works:
    print("✅ MQTT AT COMMANDS ARE WORKING!")
    print("✅ C5 is ready for AWS IoT!")
    print("\nNext steps:")
    print("1. Reconnect C5 to S3")
    print("2. Upload AWS IoT firmware to S3")
    print("3. Test AWS IoT connection")
else:
    print("❌ MQTT commands returned ERROR")
    print("Need to rebuild firmware with MQTT enabled")

ser.close()
print("\nDone!")
