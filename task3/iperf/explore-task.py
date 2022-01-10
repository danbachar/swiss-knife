#!/usr/bin/env python3

import socket
import os
import subprocess
import sys
import time
import getopt
import ipaddress
from multiprocessing.pool import ThreadPool
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

def start_server(host, port, buffer_length, connections) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)
    
    if connections > 1:
        pool = ThreadPool(processes=connections)
        speeds = []

    if isinstance(ip, ipaddress.IPv4Address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
            
            if connections > 1: 
                # parallel mode, create threads
                for i in range(connections+1):
                    #t = Thread(target=server_loop, args=(s,host, port, buffer_length))
                    speeds.append(pool.apply_async(server_loop, (s,host, port+i, buffer_length)))
            else: 
                speed = server_loop(s,host, port, buffer_length)
    elif isinstance(ip, ipaddress.IPv6Address):
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
            
            if connections > 1: 
                # parallel mode, create threads
                for i in range(connections+1):
                    #t = Thread(target=server_loop, args=(s,host, port, buffer_length))
                    speeds.append(pool.apply_async(server_loop, (s,host, port+i, buffer_length)))
            else: 
                speed = server_loop(s,host, port, buffer_length)
    else: print(f'address neither IPv4 or v6: {ip}')
    if connections > 1:
        speed = sum(map(lambda s: s.get(), speeds))
        pool.close()
    prefix, normalizedSpeed = get_prefix(speed)
    print(f'Speed achieved is {normalizedSpeed} {prefix}')
    sys.exit(1)
    

def start_client(host, port, buffer_length, duration, connections) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)
    if connections > 1:
        pool = ThreadPool(processes=connections)
        speeds = []
    
    if isinstance(ip, ipaddress.IPv4Address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
            if connections > 1: 
                # parallel mode, create threads
                for i in range(connections+1):
                    speeds.append(pool.apply_async(client_loop, (s, host, port+i, buffer_length, duration)))
            else: 
                client_loop(s, host, port, buffer_length, duration)
            
    elif isinstance(ip, ipaddress.IPv6Address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
            if connections > 1: 
                # parallel mode, create threads
                for i in range(connections+1):
                    speeds.append(pool.apply_async(client_loop, (s, host, port+i, buffer_length, duration)))
            else: 
                client_loop(s, host, port, buffer_length, duration)
    if connections > 1:
        pool.close()
    sys.exit(1)

def server_loop(sock: socket.socket, host, port, buffer_length) -> float:
    print(f'Opening server on {host}:{port}')
    sock.bind((host, port))
    sock.listen()
    conn, _ = sock.accept()
    received = 0
    firstReceive = True
    with conn:
        while True:
            data = conn.recv(buffer_length)
            if firstReceive:
                firstReceive = False
                start = time.time()
            if len(data) == 0:
                end = time.time()
                break
            length = len(data)
            #print(f'{length1} {length}')
            #if length < buffer_length:
            #    print(f'len of data < buffer length: {length}')
            received += length#buffer_length
    return received / (end-start)
    
def client_loop(sock: socket.socket, host, port, buffer_length, duration): 
    buffer = [1] * buffer_length
    b = bytes(buffer)
    print(f'connecting to {host}:{port}')
    sock.connect((host, port))
    
    end_time = time.time() + duration
    while time.time() < end_time:
        sock.send(b)
        # current_interval_start = time.time()
        #start = 0
        # while time.time() - current_interval_start < 1:
            #b = bytes(buffer[start:])
            
            #total_sent += ret
            #if ret != len(buffer[0:]):
            #    remaining = len(bytes(buffer)) - ret
            #if ret > 0:
            #    start += ret
            #    total_sent += ret
            #    if start >= len(b):
            #        start = 0
            #else: start = 0
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

    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET]) # IPv6 doesn't work yet
    addrsv6 = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6]) # IPv6 doesn't work yet
    ip = list(filter(lambda ip: "swissknife0" in ip, list(addrs)+list(addrsv6))).pop()
    #ip = list(addrs).pop()
    #ip = '169.254.68.39'
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
    serverpid = start_server(ip, port, length, connections)
    clientpid = start_client(ip, port, length, duration, connections)

    try:
        os.waitpid(serverpid, 0)
        os.waitpid(clientpid, 0)
    except ChildProcessError:
        print()

if __name__ == "__main__":
    main(sys.argv[1:])