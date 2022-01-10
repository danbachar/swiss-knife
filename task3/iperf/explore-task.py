#!/usr/bin/env python3

import socket
import os
import subprocess
import sys
import time
import getopt
import ipaddress
import netifaces as ni

PORT = 5201        # Port to listen on (non-privileged ports are > 1023)

def get_prefix(speed): 
    orderOfMagnitude = 0
    while speed > 1000:
        orderOfMagnitude += 3
        speed /= 1000

    prefix = 'bits'
    if orderOfMagnitude == 3:
        prefix = 'Kbits/s'
    if orderOfMagnitude == 6:
        prefix = 'Mbits/s'
    if orderOfMagnitude == 9:
        prefix = 'Gbits/s'
    if orderOfMagnitude == 12:
        prefix = 'Tbits/s'
    if orderOfMagnitude > 12:
        prefix = 'holybits/s'
    return prefix, speed

def start_server(host, port, buffer_length) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)

    if isinstance(ip, ipaddress.IPv4Address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, 25, bytes('swissknife0'.encode()))
            speed = server_loop(s,host, port, buffer_length)
    elif isinstance(ip, ipaddress.IPv6Address):
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, 25, bytes('swissknife0'.encode()))
            speed = server_loop(s,host, port, buffer_length)
    else: print(f'address neither IPv4 or v6: {ip}')
    prefix, normalizedSpeed = get_prefix(speed)
    print(f'Speed achieved is {normalizedSpeed} {prefix}')
    
    sys.exit(1)
    

def start_client(host, port, buffer_size, duration) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)

    if isinstance(ip, ipaddress.IPv4Address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, 25, bytes('swissknife0'.encode()))
            client_loop(s, host, port, buffer_size, duration)
            
    elif isinstance(ip, ipaddress.IPv6Address):
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, 25, bytes('swissknife0'.encode()))
            client_loop(s, host, port, buffer_size, duration)
    sys.exit(1)

def server_loop(sock: socket.socket, host, port, buffer_length) -> float:
    sock.bind((host, port))
    sock.listen()
    conn, addr = sock.accept()
    received = 0
    start= time.time()
    global end
    with conn:
        while True:
            data = conn.recv(buffer_length)
            if not data:
                end = time.time()
                break
            received += len(data)
    return received / (end-start)
    
def client_loop(sock: socket.socket, host, port, buffer_length, duration): 
    buffer = [0b1] * buffer_length
    sock.connect((host, port))
    start_time = time.time()
    total_sent = 0
    while time.time() - start_time < duration:
        current_interval_start = time.time()
        start = 0
        while time.time() - current_interval_start < 1:
            b = bytes(buffer[start:])
            ret = sock.send(b, 0)
            # if ret != len(buffer[0:]):
                # remaining = len(bytes(buffer)) - ret
            #print(f'sent {ret} bytes')
            if ret > 0:
                start += ret
                total_sent += ret
                if start >= len(b):
                    start = 0
            else: start = 0
    sock.close()
        
def open_port(port) -> None:
    # using fuser to remove blocking process from using determinated ports    
    portWithTcp = f'{str(port)}/tcp'
    process = subprocess.Popen(['fuser', '-k', portWithTcp],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True)
    while True:
            output = process.stdout.readline()
            stripped = output.strip()
            if not stripped.isspace():
                print(stripped)
            # Do something else
            return_code = process.poll()
            if return_code is not None:
                # Process has finished, read rest of the output
                for output in process.stdout.readlines():
                    stripped = output.strip()
                    if not stripped.isspace():
                        print(stripped)
                break

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv, "p:f:d:c:t:l:u",
                                   ["port=" "plot_filename=" "data_filename=" "connections=" "time=" "length=" "udp"])
    except getopt.GetoptError:
        print("Syntax Error.")
        sys.exit(2)

    #addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET]) # IPv6 doesn't work yet
    #mapped = map(lambda addr: print(addr), addrs)
    #ip = list(filter(lambda ip: "swissknife0" in ip, addrs)).pop()
    #ip = list(addrs).pop()
    ip = '169.254.68.39' # TODO: hard coded IP address
    global port
    global plot_filename
    global data_filename
    port = PORT
    connections = 1
    duration = 10
    length=128
    udp = False
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--connections"):
            connections = int(arg)
        elif opt in ("-t", "--time"):
            duration = int(arg)
            print(f'got duration of {duration}')
            
        elif opt in ("-l", "--length"):
            length = int(arg)
            print(f'got length of {length}')
        elif opt in ("-u", "--udp"):
            udp = True
            length = 1460
            
    print(f'ip: {ip}:{port}')
    
    port = int(port)
    open_port(port)
    #ip = 'fe80::e63d:1aff:fe72:f0'
    serverpid = start_server(ip, port, length)
    clientpid = start_client(ip, port, length, duration)

    try:
        os.waitpid(serverpid, 0)
        os.waitpid(clientpid, 0)
    except ChildProcessError:
        print()

if __name__ == "__main__":
    main(sys.argv[1:])