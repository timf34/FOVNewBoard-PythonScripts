#!/usr/bin/env python3
"""
Test ESP32-C5 MQTT AT Commands
This script verifies that MQTT support is enabled in the C5 firmware
"""

import serial
import time

def send_at_command(ser, command, wait_time=2):
    """Send AT command and return response"""
    print(f"\n{'='*60}")
    print(f"Sending: {command}")
    print('='*60)
    
    ser.write((command + '\r\n').encode())
    time.sleep(wait_time)
    
    response = ser.read_all().decode('utf-8', errors='ignore')
    print(f"Response:\n{response}")
    
    # Check for ERROR
    if "ERROR" in response and command.endswith("?"):
        print("❌ FAILED - Command not supported!")
        return False
    elif "OK" in response or "+" in response:
        print("✅ SUCCESS")
        return True
    else:
        print("⚠️ UNKNOWN RESPONSE")
        return None
    
    return response

def main():
    # Connect to C5
    print("\n" + "="*60)
    print("ESP32-C5 MQTT AT Command Test")
    print("="*60)
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        print(f"✅ Connected to /dev/ttyUSB0 at 115200 baud")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    time.sleep(2)
    
    # Test basic communication
    print("\n\n" + "="*60)
    print("SECTION 1: Basic Communication")
    print("="*60)
    
    send_at_command(ser, "AT")
    send_at_command(ser, "AT+GMR")
    
    # Test MQTT commands - THE CRITICAL TEST
    print("\n\n" + "="*60)
    print("SECTION 2: MQTT Command Support (CRITICAL)")
    print("="*60)
    
    mqtt_tests = {
        "AT+MQTTUSERCFG": "MQTT User Configuration",
        "AT+MQTTCONNCFG": "MQTT Connection Configuration",
        "AT+MQTTCONN": "MQTT Connection",
        "AT+MQTTSUB": "MQTT Subscribe",
        "AT+MQTTPUB": "MQTT Publish",
        "AT+MQTTCLEAN": "MQTT Clean Session",
    }
    
    mqtt_working = True
    for cmd, description in mqtt_tests.items():
        print(f"\nTesting: {description}")
        result = send_at_command(ser, f"{cmd}=?", wait_time=2)
        if result == False:
            mqtt_working = False
    
    # Test SSL/TLS commands
    print("\n\n" + "="*60)
    print("SECTION 3: SSL/TLS Support")
    print("="*60)
    
    send_at_command(ser, "AT+CIPSSLCCONF=?", wait_time=2)
    
    # Test WiFi commands
    print("\n\n" + "="*60)
    print("SECTION 4: WiFi Commands")
    print("="*60)
    
    send_at_command(ser, "AT+CWMODE?")
    send_at_command(ser, "AT+CWJAP?")
    
    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if mqtt_working:
        print("✅ MQTT AT Commands: ENABLED")
        print("✅ Your C5 firmware is ready for AWS IoT!")
        print("\nNext steps:")
        print("1. Reconnect C5 to S3")
        print("2. Upload AWS IoT firmware to S3")
        print("3. Test AWS IoT connection")
    else:
        print("❌ MQTT AT Commands: NOT ENABLED")
        print("❌ MQTT support was not compiled into firmware")
        print("\nYou need to:")
        print("1. Run ./build.py menuconfig again")
        print("2. Enable AT MQTT command support")
        print("3. Rebuild and reflash")
    
    ser.close()
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
