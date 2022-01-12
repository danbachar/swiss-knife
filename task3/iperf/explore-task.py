#!/usr/bin/env python3

import socket
import os
import sys
import time as timeModule
import getopt
import ipaddress
from queue import Queue
from threading import Thread
import netifaces as ni

# Adapted from https://stackoverflow.com/a/7257510
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks, retVal = 0):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                self.retVal = func(*args, **kargs)
            except Exception as e:
                print("exception silenced", e)
            finally:
                self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        self.workers = []
        for _ in range(num_threads):
            self.workers.append(Worker(self.tasks))
            # print(f'workers has {len(self.workers)} length')

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
        
    def wait_completion_and_return_sum(self) -> float: 
        sum = 0
        self.wait_completion()
        
        for worker in self.workers:
            sum += worker.retVal[0]
        
        return sum

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

def create_client_socket_and_connect(reverse, udp, ip, port, buffer_length, duration, mss) -> float:
    s = create_socket(udp, ip, buffer_length, mss)
    client_loop(reverse, udp, s, ip, port, buffer_length, duration)
    
def create_socket(udp, ip, buffer_length, mss) -> socket.socket:
    stream = ''
    if udp:
        stream = socket.SOCK_DGRAM
    else: stream= socket.SOCK_STREAM
    if isinstance(ip, ipaddress.IPv4Address):
        s = socket.socket(socket.AF_INET, stream)
    elif isinstance(ip, ipaddress.IPv6Address):
        s = socket.socket(socket.AF_INET6, stream)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
    s.settimeout(1.0)
    
    if mss:
        s.setsockopt(socket.SOL_SOCKET, socket.TCP_MAXSEG, mss)
    return s

def start_server(reverse, udp, host, port, buffer_length, connections, duration, mss) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)
    
    s = create_socket(udp, ip, buffer_length, mss)
    s.bind((str(ip), port))
    if not udp:
        s.listen()
    
    speed = 0
    if connections > 1:
        pool = ThreadPool(connections)
        for _ in range(connections):
            pool.add_task(server_loop, reverse, udp, s, buffer_length, duration)
        begin = timeModule.time()
        bits = pool.wait_completion_and_return_sum()
        duration = timeModule.time() - begin
        speed = bits/duration
    else:
        (bits,time) = server_loop(reverse, udp, s, buffer_length, duration)
        speed = (bits/time)
    prefix, normalizedSpeed = get_prefix(speed)

    print(f'Speed achieved is {normalizedSpeed} {prefix}')
    sys.exit(1)
    
def start_client(reverse, udp, host, port, buffer_length, duration, connections, mss) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)
    if connections > 1:
        pool = ThreadPool(connections)
        for _ in range(connections):
            pool.add_task(create_client_socket_and_connect, reverse, udp, ip, port, buffer_length, duration, mss)
        pool.wait_completion()
    else:
        s = create_socket(udp, ip, buffer_length, mss)
        client_loop(reverse, udp, s, host, port, buffer_length, duration)
    sys.exit(1)

def server_loop(reverse, udp, sock: socket.socket, buffer_length, duration):
    if not udp:
        conn, _ = sock.accept()
    buffer = [1] * (buffer_length+1)
    b = bytes(buffer)
    received = 0
    firstReceive = True
    while True:
        if not reverse:
            if not udp:
                data = conn.recv(buffer_length)
                if firstReceive:
                    firstReceive = False
                    start = timeModule.time()
            else: data, _ = sock.recvfrom(buffer_length)
            if not data:
                end = timeModule.time()
                break;
            length = len(data)
            received += length
        else:
            end_time = timeModule.time() + duration
            while timeModule.time() < end_time:
            # reverse mode, TCP is assumed because UDP doesn't work
                length = conn.send(b)
                if firstReceive:
                    firstReceive = False
                    start = timeModule.time()
                received += length
            end = timeModule.time()
            conn.close()
            break
    return (received,end-start)
    
def client_loop(reverse, udp, sock: socket.socket, host, port, buffer_length, duration): 
    buffer = [1] * buffer_length
    b = bytes(buffer)
    if not udp:
        sock.connect((str(host), port))
    end_time = timeModule.time() + duration
    if not reverse:
        while timeModule.time() < end_time:
            if not udp:
                sock.send(b)
            else: sock.sendto(b, (host, port))
    else: 
        while True:
            if not udp:
                data = sock.recv(buffer_length)
            else: data, _ = sock.recvfrom(buffer_length)
            if not data:
                break
    if not udp and not reverse:
        sock.close()
        
def main(argv) -> None:
    try:
        opts, _ = getopt.getopt(argv, "p:f:d:c:t:l:uRM:",
                                   ["port=" "plot_filename=" "data_filename=" "connections=" "time=" "length=" "udp", "reverse" "set-mss"])
    except getopt.GetoptError:
        print("Syntax Error.")
        sys.exit(2)

    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET]) # IPv6 doesn't work yet
    addrsv6 = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6]) # IPv6 doesn't work yet
    ip = list(filter(lambda ip: "swissknife0" in ip, list(addrs)+list(addrsv6))).pop()
    global port
    global plot_filename
    global data_filename
    port = PORT
    connections = 1
    duration = 10
    length=128
    udp = False
    reverse = False
    mss = 0
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--connections"):
            connections = int(arg)
            print(f'benchmarking with {connections} connections, this might take a while...')
        elif opt in ("-t", "--time"):
            duration = int(arg)
        elif opt in ("-l", "--length"):
            length = int(arg)
        elif opt in ("-u", "--udp"):
            udp = True
            length = 1460
        elif opt in ("-R", "--reverse"):
            reverse = True
        elif opt in ("-M", "--set-mss"):
            mss = int(arg)        
    
    port = int(port)

    serverpid = start_server(reverse, udp, ip, port, length, connections, duration, mss)
    clientpid = start_client(reverse, udp, ip, port, length, duration, connections, mss)

    try:
        os.waitpid(serverpid, 0)
        os.waitpid(clientpid, 0)
    except ChildProcessError:
        print()

if __name__ == "__main__":
    main(sys.argv[1:])