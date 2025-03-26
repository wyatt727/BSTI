#!/usr/bin/env python3
# STARTFILES
# up.txt "Alive Targets"
# ENDFILES
# ARGS
# TARGETS_PATH "Path to target file on drone, probably /tmp/up.txt"
# ENDARGS
# AUTHOR: Connor Fancy

import dns.resolver
import dns.reversename
import ipaddress
import sys
import threading
import queue

def dns_lookup(q):
    while not q.empty():
        ip = q.get()
        try:
            reversed_dns = dns.reversename.from_address(ip)
            answer = dns.resolver.resolve(reversed_dns, "PTR")
            print(f"{ip} - {answer[0]}")
        except:
            pass
        q.task_done()

def process_input(input_arg):
    try:
        for ip in ipaddress.IPv4Network(input_arg):
            yield str(ip)
    except ValueError:
        with open(input_arg, 'r') as file:
            for line in file:
                line = line.strip()
                try:
                    for ip in ipaddress.IPv4Network(line):
                        yield str(ip)
                except ValueError:
                    yield line

def main():
    if len(sys.argv) != 2:
        print("Usage: python ip2dns.py <subnet/file>")
        sys.exit(1)

    ip_queue = queue.Queue()
    for ip in process_input(sys.argv[1]):
        ip_queue.put(ip)

    num_threads = 10
    threads = []

    for _ in range(num_threads):
        thread = threading.Thread(target=dns_lookup, args=(ip_queue,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
