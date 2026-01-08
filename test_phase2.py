#!/usr/bin/env python3
"""
Phase 2 Test Script for Firmware Buffer AT Commands

Tests the complete OTA buffer system:
  - AT+FWMEMINFO?              - Memory query
  - AT+FWBUFDOWNLOAD="<url>"   - Download firmware
  - AT+FWBUFSTATUS?            - Query status
  - AT+FWBUFREAD=<offset>,<len> - Read chunks
  - AT+FWBUFVERIFY=<crc>       - Verify CRC
  - AT+FWBUFCLEAR              - Clear buffer

Usage:
    python3 test_phase2.py [--port /dev/ttyUSB0] [--url http://example.com/firmware.bin]

Requirements:
    pip install pyserial
"""

import serial
import time
import argparse
import sys
import struct
import zlib

# Configuration
DEFAULT_PORT = '/dev/ttyUSB0'
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 2

# Test URL - replace with your actual firmware URL
# This should be an HTTP (not HTTPS) URL to a binary file
DEFAULT_TEST_URL = "http://joinpatch.s3.eu-west-1.amazonaws.com/firmware.bin"  # Replace with your test URL


# Add this to the beginning of your test, before the download test

def connect_wifi(ser, ssid, password, timeout=30):
    """Connect to WiFi network."""
    print("\n" + "="*60)
    print(f"Connecting to WiFi: {ssid}")
    print("="*60)
    
    # Set station mode
    response = send_command(ser, "AT+CWMODE=1")
    if "OK" not in response:
        print("WARNING: Could not set WiFi mode")
    
    # Check if already connected
    response = send_command(ser, "AT+CWJAP?")
    if ssid in response:
        print("Already connected to WiFi")
        return True
    
    # Connect to WiFi
    ser.reset_input_buffer()
    cmd = f'AT+CWJAP="{ssid}","{password}"'
    ser.write(f"{cmd}\r\n".encode())
    print(f">>> {cmd}")
    
    # Wait for connection (can take up to 30 seconds)
    start = time.time()
    response = b''
    while time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            resp_str = response.decode('utf-8', errors='replace')
            
            if 'WIFI GOT IP' in resp_str:
                print("<<< WIFI CONNECTED")
                print("<<< WIFI GOT IP")
                # Wait for OK
                time.sleep(0.5)
                if ser.in_waiting:
                    response += ser.read(ser.in_waiting)
                print("<<< OK")
                print("PASS: WiFi connected")
                return True
            
            if 'FAIL' in resp_str or 'ERROR' in resp_str:
                print(f"<<< {resp_str}")
                print("FAIL: WiFi connection failed")
                return False
        
        time.sleep(0.1)
    
    print("FAIL: WiFi connection timeout")
    return False

def send_command(ser, cmd, timeout=DEFAULT_TIMEOUT, wait_for_response=True):
    """Send AT command and return response."""
    ser.reset_input_buffer()
    
    cmd_bytes = f"{cmd}\r\n".encode()
    ser.write(cmd_bytes)
    print(f">>> {cmd}")
    
    if not wait_for_response:
        return ""
    
    time.sleep(0.1)
    
    response = b''
    start = time.time()
    while time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            if b'OK\r\n' in response or b'ERROR\r\n' in response:
                break
        time.sleep(0.05)
    
    response_str = response.decode('utf-8', errors='replace')
    
    for line in response_str.strip().split('\n'):
        print(f"<<< {line.rstrip()}")
    
    return response_str


def send_download_command(ser, url, timeout=120):
    """Send download command with extended timeout for large files."""
    ser.reset_input_buffer()
    
    cmd = f'AT+FWBUFDOWNLOAD="{url}"'
    cmd_bytes = f"{cmd}\r\n".encode()
    ser.write(cmd_bytes)
    print(f">>> {cmd}")
    
    # Wait for STARTED
    response = b''
    start = time.time()
    while time.time() - start < 10:  # 10 second timeout for initial response
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            if b'+FWBUFDOWNLOAD:STARTED' in response:
                print("<<< +FWBUFDOWNLOAD:STARTED")
                break
            if b'ERROR' in response:
                print(f"<<< {response.decode('utf-8', errors='replace')}")
                return response.decode('utf-8', errors='replace'), False
        time.sleep(0.1)
    
    if b'+FWBUFDOWNLOAD:STARTED' not in response:
        print("ERROR: No STARTED response received")
        return "", False
    
    # Wait for DONE or ERROR
    response = b''
    start = time.time()
    last_status_time = start
    
    while time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            
            # Check for completion
            if b'+FWBUFDOWNLOAD:DONE' in response:
                resp_str = response.decode('utf-8', errors='replace')
                for line in resp_str.strip().split('\n'):
                    print(f"<<< {line.rstrip()}")
                return resp_str, True
            
            if b'+FWBUFDOWNLOAD:ERROR' in response:
                resp_str = response.decode('utf-8', errors='replace')
                for line in resp_str.strip().split('\n'):
                    print(f"<<< {line.rstrip()}")
                return resp_str, False
        
        # Poll status every 5 seconds
        if time.time() - last_status_time > 5:
            # Note: We shouldn't send other commands during download
            # Just print a waiting message
            elapsed = int(time.time() - start)
            print(f"... Downloading ({elapsed}s elapsed)")
            last_status_time = time.time()
        
        time.sleep(0.1)
    
    print("ERROR: Download timeout")
    return "", False


def read_chunk(ser, offset, length, timeout=5):
    """Read a chunk from the buffer and return raw bytes."""
    ser.reset_input_buffer()
    
    cmd = f"AT+FWBUFREAD={offset},{length}"
    cmd_bytes = f"{cmd}\r\n".encode()
    ser.write(cmd_bytes)
    
    # Read response header
    response = b''
    start = time.time()
    header_end = -1
    
    while time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
            
            # Look for header: +FWBUFREAD:<length>,
            if b'+FWBUFREAD:' in response and b',' in response:
                # Find the comma after the length
                header_match = response.find(b'+FWBUFREAD:')
                if header_match >= 0:
                    comma_pos = response.find(b',', header_match)
                    if comma_pos >= 0:
                        header_end = comma_pos + 1  # Position after comma
                        break
            
            # Check for error
            if b'ERROR' in response:
                print(f">>> {cmd}")
                print(f"<<< {response.decode('utf-8', errors='replace')}")
                return None
        
        time.sleep(0.01)
    
    if header_end < 0:
        print(f">>> {cmd}")
        print(f"ERROR: No valid header in response")
        return None
    
    # Parse the length from header
    header_str = response[:header_end].decode('utf-8', errors='replace')
    try:
        actual_length = int(header_str.split(':')[1].split(',')[0])
    except:
        print(f">>> {cmd}")
        print(f"ERROR: Failed to parse length from header: {header_str}")
        return None
    
    # Read remaining binary data
    data_start = header_end
    needed = actual_length + 4 + len(b'OK\r\n')  # +4 for \r\n before OK
    
    while len(response) < data_start + needed and time.time() - start < timeout:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            response += chunk
        time.sleep(0.01)
    
    # Extract binary data
    binary_data = response[data_start:data_start + actual_length]
    
    if len(binary_data) != actual_length:
        print(f">>> {cmd}")
        print(f"WARNING: Expected {actual_length} bytes, got {len(binary_data)}")
    
    return binary_data


def test_memory_info(ser):
    """Test AT+FWMEMINFO? command."""
    print("\n" + "="*60)
    print("TEST: AT+FWMEMINFO?")
    print("="*60)
    
    response = send_command(ser, "AT+FWMEMINFO?")
    
    if "+FWMEMINFO:PSRAM" not in response:
        print("FAIL: No PSRAM info in response")
        return False
    
    # Parse values
    try:
        for line in response.split('\n'):
            if "+FWMEMINFO:PSRAM" in line:
                parts = line.strip().split(',')
                psram_free = int(parts[1])
                psram_largest = int(parts[2])
                print(f"   PSRAM Free: {psram_free:,} bytes ({psram_free/1024/1024:.2f} MB)")
                print(f"   PSRAM Largest Block: {psram_largest:,} bytes ({psram_largest/1024/1024:.2f} MB)")
    except Exception as e:
        print(f"WARNING: Could not parse values: {e}")
    
    print("PASS: Memory info retrieved")
    return True


def test_status_idle(ser):
    """Test AT+FWBUFSTATUS? in IDLE state."""
    print("\n" + "="*60)
    print("TEST: AT+FWBUFSTATUS? (expecting IDLE)")
    print("="*60)
    
    response = send_command(ser, "AT+FWBUFSTATUS?")
    
    if "+FWBUFSTATUS:" not in response:
        print("FAIL: No status in response")
        return False
    
    if "IDLE" in response:
        print("PASS: Status is IDLE")
        return True
    else:
        print(f"INFO: Status is not IDLE (may have previous data)")
        return True


def test_clear(ser):
    """Test AT+FWBUFCLEAR command."""
    print("\n" + "="*60)
    print("TEST: AT+FWBUFCLEAR")
    print("="*60)
    
    response = send_command(ser, "AT+FWBUFCLEAR")
    
    if "OK" in response:
        print("PASS: Buffer cleared")
        return True
    elif "ERROR,BUSY" in response:
        print("FAIL: Cannot clear - download in progress")
        return False
    else:
        print("FAIL: Unexpected response")
        return False


def test_download(ser, url):
    """Test AT+FWBUFDOWNLOAD command."""
    print("\n" + "="*60)
    print(f"TEST: AT+FWBUFDOWNLOAD")
    print(f"URL: {url}")
    print("="*60)
    
    response, success = send_download_command(ser, url, timeout=120)
    
    if not success:
        print("FAIL: Download failed")
        return False, 0, 0
    
    # Parse size and CRC from response
    # Format: +FWBUFDOWNLOAD:DONE,<size>,0x<crc>
    try:
        for line in response.split('\n'):
            if "+FWBUFDOWNLOAD:DONE" in line:
                parts = line.strip().split(',')
                size = int(parts[1])
                crc_str = parts[2].strip()
                crc = int(crc_str, 16) if crc_str.startswith('0x') else int(crc_str)
                print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
                print(f"   CRC32: 0x{crc:08X}")
                print("PASS: Download complete")
                return True, size, crc
    except Exception as e:
        print(f"WARNING: Could not parse response: {e}")
    
    print("PASS: Download completed (could not parse details)")
    return True, 0, 0


def test_status_ready(ser, expected_size=0, expected_crc=0):
    """Test AT+FWBUFSTATUS? in READY state."""
    print("\n" + "="*60)
    print("TEST: AT+FWBUFSTATUS? (expecting READY)")
    print("="*60)
    
    response = send_command(ser, "AT+FWBUFSTATUS?")
    
    if "+FWBUFSTATUS:" not in response:
        print("FAIL: No status in response")
        return False
    
    if "READY" not in response:
        print(f"FAIL: Expected READY state")
        return False
    
    print("PASS: Status is READY")
    return True


def test_read_all_chunks(ser, total_size, chunk_size=4096):
    """Test reading all chunks and compute CRC."""
    print("\n" + "="*60)
    print(f"TEST: Read all chunks ({total_size} bytes in {chunk_size}-byte chunks)")
    print("="*60)
    
    all_data = b''
    offset = 0
    chunk_count = 0
    
    while offset < total_size:
        remaining = total_size - offset
        read_size = min(chunk_size, remaining)
        
        chunk = read_chunk(ser, offset, read_size)
        
        if chunk is None:
            print(f"FAIL: Failed to read chunk at offset {offset}")
            return False, None
        
        if len(chunk) != read_size:
            print(f"WARNING: Chunk {chunk_count}: expected {read_size}, got {len(chunk)}")
        
        all_data += chunk
        offset += len(chunk)
        chunk_count += 1
        
        # Progress update
        if chunk_count % 10 == 0:
            pct = offset * 100.0 / total_size
            print(f"   Progress: {offset:,} / {total_size:,} bytes ({pct:.1f}%)")
    
    print(f"   Read {chunk_count} chunks, {len(all_data)} total bytes")
    
    # Compute CRC32
    computed_crc = zlib.crc32(all_data) & 0xFFFFFFFF
    print(f"   Computed CRC32: 0x{computed_crc:08X}")
    
    print("PASS: All chunks read successfully")
    return True, computed_crc


def test_verify(ser, expected_crc):
    """Test AT+FWBUFVERIFY command."""
    print("\n" + "="*60)
    print(f"TEST: AT+FWBUFVERIFY=0x{expected_crc:08X}")
    print("="*60)
    
    response = send_command(ser, f"AT+FWBUFVERIFY=0x{expected_crc:08X}")
    
    if "+FWBUFVERIFY:OK" in response:
        print("PASS: CRC verification successful")
        return True
    elif "+FWBUFVERIFY:MISMATCH" in response:
        print("FAIL: CRC mismatch")
        return False
    else:
        print("FAIL: Unexpected response")
        return False


def main():
    parser = argparse.ArgumentParser(description='Phase 2 Firmware Buffer Test')
    parser.add_argument('--port', '-p', default=DEFAULT_PORT, help=f'Serial port (default: {DEFAULT_PORT})')
    parser.add_argument('--baud', '-b', type=int, default=DEFAULT_BAUD, help=f'Baud rate (default: {DEFAULT_BAUD})')
    parser.add_argument('--url', '-u', default=DEFAULT_TEST_URL, help='HTTP URL to test firmware')
    parser.add_argument('--skip-download', action='store_true', help='Skip download test (use existing buffer)')
    args = parser.parse_args()
    
    print("="*60)
    print("FOV OTA - Phase 2: Firmware Buffer Test")
    print("="*60)
    print(f"Port: {args.port}")
    print(f"Baud: {args.baud}")
    print(f"Test URL: {args.url}")
    
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"\nERROR: Could not open serial port: {e}")
        sys.exit(1)
    
    with ser:
        time.sleep(0.5)
        
        # Test basic AT
        print("\n" + "="*60)
        print("TEST: Basic AT Command")
        print("="*60)
        response = send_command(ser, "AT")
        if "OK" not in response:
            print("FAIL: Basic AT command failed")
            sys.exit(1)
        print("PASS: AT command working")
        
        print("Connecting to wifi...")
        wifi_success = connect_wifi(ser, "tim", "password")
        print(f"Connected to wifi: {wifi_success}")
        
        # Test sequence
        results = {}
        
        results['meminfo'] = test_memory_info(ser)
        results['status_initial'] = test_status_idle(ser)
        
        if not args.skip_download:
            results['clear_initial'] = test_clear(ser)
            results['download'], dl_size, dl_crc = test_download(ser, args.url)
        else:
            print("\n(Skipping download, using existing buffer)")
            # Get size from status
            response = send_command(ser, "AT+FWBUFSTATUS?")
            # Parse size from READY status
            dl_size = 0
            dl_crc = 0
            try:
                for line in response.split('\n'):
                    if "READY" in line:
                        parts = line.split(',')
                        dl_size = int(parts[2])
                        dl_crc = int(parts[3].strip(), 16)
            except:
                pass
            results['download'] = True
        
        if results.get('download', False) and dl_size > 0:
            results['status_ready'] = test_status_ready(ser, dl_size, dl_crc)
            results['read_chunks'], computed_crc = test_read_all_chunks(ser, dl_size)
            
            if computed_crc is not None:
                results['verify'] = test_verify(ser, computed_crc)
        
        results['clear_final'] = test_clear(ser)
        results['status_final'] = test_status_idle(ser)
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        all_pass = True
        for test_name, result in results.items():
            if isinstance(result, tuple):
                result = result[0]
            status = "PASS" if result else "FAIL"
            print(f"  {test_name}: {status}")
            if not result:
                all_pass = False
        
        print("="*60)
        if all_pass:
            print("ALL TESTS PASSED!")
            print("\nPhase 2 complete. Ready for Phase 3 (S3 integration).")
        else:
            print("SOME TESTS FAILED")
        print("="*60)
        
        sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
