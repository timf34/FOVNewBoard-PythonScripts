#!/usr/bin/env python3
"""
Test script for AT+FWMEMINFO? command - Phase 1 of FOV OTA Implementation

This script tests the custom AT command that reports PSRAM availability
on the ESP32-C5 WiFi modem.

Usage:
    python3 test_meminfo.py [--port /dev/ttyUSB1]
    
Requirements:
    pip install pyserial
"""

import serial
import time
import argparse
import sys

# Default configuration
DEFAULT_PORT = '/dev/ttyUSB0'  # AT command port (usually USB1 if USB0 is flash)
DEFAULT_BAUD = 115200
TIMEOUT = 2  # seconds

# Minimum PSRAM required for OTA (1.5MB)
MIN_PSRAM_BYTES = 1572864


def send_at_command(ser, cmd, timeout=TIMEOUT):
    """
    Send AT command and return response.
    
    Args:
        ser: Serial port object
        cmd: AT command string (without \r\n)
        timeout: Response timeout in seconds
        
    Returns:
        Response string
    """
    # Clear any pending data
    ser.reset_input_buffer()
    
    # Send command
    cmd_bytes = f"{cmd}\r\n".encode()
    ser.write(cmd_bytes)
    print(f">>> {cmd}")
    
    # Small delay for command processing
    time.sleep(0.1)
    
    # Read response
    response = b''
    start = time.time()
    while time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            # Check for response terminators
            if b'OK\r\n' in response or b'ERROR\r\n' in response:
                break
        time.sleep(0.05)
    
    response_str = response.decode('utf-8', errors='replace')
    
    # Print response with indentation
    for line in response_str.strip().split('\n'):
        print(f"<<< {line}")
    
    return response_str


def parse_meminfo_response(response):
    """
    Parse AT+FWMEMINFO? response.
    
    Args:
        response: Response string from AT+FWMEMINFO?
        
    Returns:
        dict with psram and internal memory info, or None on parse error
    """
    result = {
        'psram_free': 0,
        'psram_largest': 0,
        'internal_free': 0,
        'internal_largest': 0
    }
    
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('+FWMEMINFO:PSRAM,'):
            parts = line.split(',')
            if len(parts) >= 3:
                try:
                    result['psram_free'] = int(parts[1])
                    result['psram_largest'] = int(parts[2])
                except ValueError:
                    pass
        elif line.startswith('+FWMEMINFO:INTERNAL,'):
            parts = line.split(',')
            if len(parts) >= 3:
                try:
                    result['internal_free'] = int(parts[1])
                    result['internal_largest'] = int(parts[2])
                except ValueError:
                    pass
    
    return result


def format_bytes(b):
    """Format bytes as human-readable string"""
    if b >= 1024 * 1024:
        return f"{b:,} bytes ({b/1024/1024:.2f} MB)"
    elif b >= 1024:
        return f"{b:,} bytes ({b/1024:.1f} KB)"
    else:
        return f"{b:,} bytes"


def main():
    parser = argparse.ArgumentParser(
        description='Test AT+FWMEMINFO? command on ESP32-C5'
    )
    parser.add_argument(
        '--port', '-p',
        default=DEFAULT_PORT,
        help=f'Serial port (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int,
        default=DEFAULT_BAUD,
        help=f'Baud rate (default: {DEFAULT_BAUD})'
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("FOV OTA - Phase 1: Memory Verification Test")
    print("=" * 60)
    print(f"\nConnecting to {args.port} at {args.baud} baud...")
    
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"\nERROR: Could not open serial port: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that the device is connected")
        print("  2. Check the port name (try ls /dev/ttyUSB*)")
        print("  3. Check permissions (try: sudo chmod 666 /dev/ttyUSB1)")
        print("  4. Make sure no other program is using the port")
        sys.exit(1)
    
    with ser:
        # Wait for connection to stabilize
        time.sleep(0.5)
        
        # Test 1: Basic AT command
        print("\n" + "-" * 40)
        print("Test 1: Basic AT Command")
        print("-" * 40)
        
        response = send_at_command(ser, "AT")
        
        if 'OK' not in response:
            print("\n❌ FAILED: Basic AT command did not respond with OK")
            print("\nTroubleshooting:")
            print("  1. Check that you're connected to the AT command port")
            print("     (not the debug/flash port)")
            print("  2. Try resetting the ESP32-C5")
            print("  3. Check baud rate matches ESP-AT configuration")
            sys.exit(1)
        
        print("\n✓ Basic AT command working")
        
        # Test 2: AT+FWMEMINFO?
        print("\n" + "-" * 40)
        print("Test 2: AT+FWMEMINFO Command")
        print("-" * 40)
        
        response = send_at_command(ser, "AT+FWMEMINFO")
        
        if 'ERROR' in response and '+FWMEMINFO' not in response:
            print("\n❌ FAILED: AT+FWMEMINFO? command not recognized")
            print("\nThe custom command is not registered. Check:")
            print("  1. at_fw_buffer_cmd.c is in components/at/src/")
            print("  2. File is listed in components/at/CMakeLists.txt")
            print("  3. at_fw_buffer_cmd_register() is called during init")
            print("  4. Firmware was rebuilt and reflashed after changes")
            sys.exit(1)
        
        if '+FWMEMINFO:PSRAM' not in response:
            print("\n❌ FAILED: Unexpected response format")
            sys.exit(1)
        
        print("\n✓ AT+FWMEMINFO? command recognized")
        
        # Parse and analyze results
        mem = parse_meminfo_response(response)
        
        print("\n" + "=" * 60)
        print("MEMORY ANALYSIS")
        print("=" * 60)
        
        # PSRAM Analysis
        print("\n📊 PSRAM (External SPI RAM):")
        print(f"   Free:          {format_bytes(mem['psram_free'])}")
        print(f"   Largest block: {format_bytes(mem['psram_largest'])}")
        
        if mem['psram_largest'] == 0:
            print("\n   ❌ STATUS: NO PSRAM DETECTED")
            print("\n   This is a critical problem. PSRAM is required for OTA buffering.")
            print("   Check:")
            print("     1. CONFIG_SPIRAM=y in sdkconfig")
            print("     2. PSRAM hardware is present and working")
            print("     3. PSRAM mode matches your hardware")
            psram_ok = False
        elif mem['psram_largest'] < MIN_PSRAM_BYTES:
            print(f"\n   ⚠️  STATUS: INSUFFICIENT (need {format_bytes(MIN_PSRAM_BYTES)})")
            print("\n   The largest contiguous block is smaller than required.")
            print("   This might be due to memory fragmentation.")
            print("   Try resetting the device for a fresh memory state.")
            psram_ok = False
        else:
            print(f"\n   ✓ STATUS: SUFFICIENT for {format_bytes(MIN_PSRAM_BYTES)} firmware")
            psram_ok = True
        
        # Internal RAM Analysis
        print("\n📊 Internal RAM:")
        print(f"   Free:          {format_bytes(mem['internal_free'])}")
        print(f"   Largest block: {format_bytes(mem['internal_largest'])}")
        
        # Overall verdict
        print("\n" + "=" * 60)
        if psram_ok:
            print("✅ PHASE 1 PASSED: Memory verification successful!")
            print("=" * 60)
            print("\nYou are ready to proceed to Phase 2: Basic Download")
            print("\nNext steps:")
            print("  1. Implement AT+FWBUFDOWNLOAD")
            print("  2. Implement AT+FWBUFSTATUS?")
            print("  3. Implement AT+FWBUFCLEAR")
            sys.exit(0)
        else:
            print("❌ PHASE 1 FAILED: Memory verification unsuccessful")
            print("=" * 60)
            print("\nResolve the PSRAM issues before proceeding.")
            sys.exit(1)


if __name__ == "__main__":
    main()
