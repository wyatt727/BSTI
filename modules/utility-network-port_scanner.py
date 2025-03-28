#!/usr/bin/env python3
# STARTFILES
# targets.txt "List of IP addresses or hostnames to scan, one per line"
# ENDFILES
# ARGS
# PORTS "Comma-separated list of ports to scan (e.g., 80,443,8080) or a range (e.g., 1-1000)"
# TIMEOUT "Connection timeout in seconds (default: 1)"
# ENDARGS
# AUTHOR: Security Tester

import socket
import sys
import concurrent.futures
import time
from datetime import datetime

def scan_port(target, port, timeout):
    """Scan a single port on a target."""
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        
        # Attempt to connect to the port
        result = s.connect_ex((target, port))
        s.close()
        
        # If the connection was successful (result = 0), the port is open
        if result == 0:
            return port, "Open"
        return port, "Closed"
    except socket.gaierror:
        return port, "Error: Hostname could not be resolved"
    except socket.error:
        return port, "Error: Could not connect to server"
    except Exception as e:
        return port, f"Error: {str(e)}"

def main():
    # Get command line arguments
    if len(sys.argv) < 2:
        print("Usage: python port_scanner.py [PORTS] (TIMEOUT)")
        sys.exit(1)
    
    ports_arg = sys.argv[1]
    timeout = 1  # Default timeout
    
    if len(sys.argv) > 2:
        try:
            timeout = float(sys.argv[2])
        except ValueError:
            print("Timeout must be a number")
            sys.exit(1)
    
    # Parse ports argument
    ports_to_scan = []
    
    if '-' in ports_arg:
        # Port range
        try:
            start, end = map(int, ports_arg.split('-'))
            ports_to_scan = list(range(start, end + 1))
        except ValueError:
            print("Invalid port range format. Use: start-end")
            sys.exit(1)
    else:
        # Comma-separated ports
        try:
            ports_to_scan = [int(p) for p in ports_arg.split(',')]
        except ValueError:
            print("Invalid port format. Use comma-separated numbers or a range.")
            sys.exit(1)
    
    # Read targets from file
    try:
        with open('/tmp/targets.txt', 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: targets.txt file not found")
        sys.exit(1)
    
    if not targets:
        print("No targets found in targets.txt")
        sys.exit(1)
    
    print(f"Starting port scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scanning {len(targets)} target(s) for {len(ports_to_scan)} port(s) with timeout {timeout}s\n")
    
    # Scan each target
    for target in targets:
        print(f"\nScanning target: {target}")
        print("=" * 50)
        
        start_time = time.time()
        open_ports = 0
        
        # Use ThreadPoolExecutor to scan ports concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(50, len(ports_to_scan))) as executor:
            future_to_port = {
                executor.submit(scan_port, target, port, timeout): port
                for port in ports_to_scan
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_port):
                port, status = future.result()
                if status == "Open":
                    open_ports += 1
                    service = ""
                    try:
                        service = socket.getservbyport(port)
                    except:
                        pass
                    
                    service_info = f" - {service}" if service else ""
                    print(f"Port {port}/tcp: {status}{service_info}")
        
        scan_duration = time.time() - start_time
        print(f"\nScan completed in {scan_duration:.2f} seconds")
        print(f"Found {open_ports} open port(s) on {target}")
    
    print(f"\nPort scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 