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
import json as jsonModule

# Adapted from https://stackoverflow.com/a/7257510
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks, retVal = 0, packetsSent = 0):
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
        
    def wait_completion_and_return_sum_and_packets(self): 
        sum = 0
        packets = 0
        self.wait_completion()
        
        for worker in self.workers:
            sum += worker.retVal[0]
            packets += worker.retVal[2]
        
        return (sum, packets)

class Measurement:
    def __init__(self, download, upload, loss, jitter):
        self.download = download
        self.upload = upload
        self.loss = loss
        self.jitter = jitter
    
PORT = 5201        # Port to listen on (non-privileged ports are > 1023)

def get_prefix(speed):
    spd = speed
    orderOfMagnitude = 0
    while spd > 1000:
        orderOfMagnitude += 3
        spd /= 1000

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
    return prefix, spd

def create_client_socket_and_connect(reverse, udp, ip, port, buffer_length, duration, mss, zerocopy):
    s = create_socket(udp, ip, buffer_length, mss)
    return client_loop(reverse, udp, s, ip, port, buffer_length, duration, zerocopy)
    
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
    s.settimeout(5.0)
    
    if mss:
        s.setsockopt(socket.SOL_SOCKET, socket.TCP_MAXSEG, mss)
    return s

def start_server(reverse, udp, host, port, buffer_length, connections, duration, mss, zerocopy):
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
            pool.add_task(server_loop, reverse, udp, s, buffer_length, duration, zerocopy)
        begin = timeModule.time()
        (bits, packets) = pool.wait_completion_and_return_sum_and_packets()
        duration = timeModule.time() - begin
    else:
        (bits,duration,packets) = server_loop(reverse, udp, s, buffer_length, duration, zerocopy)
    speed = (bits/duration)
    speed *= 8 # everything is bytes
    
    with open('server-res.txt', 'w') as resfile:
        resfile.write(f'{speed},{packets}')
        resfile.flush()
    sys.exit(1)
    
def start_client(reverse, udp, host, port, buffer_length, duration, connections, mss, zerocopy) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    timeModule.sleep(1)
    ip = ipaddress.ip_address(host)
    if connections > 1:
        pool = ThreadPool(connections)
        for _ in range(connections):
            pool.add_task(create_client_socket_and_connect, reverse, udp, ip, port, buffer_length, duration, mss, zerocopy)
        begin = timeModule.time()
        (bits, packets) = pool.wait_completion_and_return_sum_and_packets()
        duration = timeModule.time() - begin
    else:
        s = create_socket(udp, ip, buffer_length, mss)
        (bits, duration, packets) = client_loop(reverse, udp, s, host, port, buffer_length, duration, zerocopy)
    with open('client-res.txt', 'w') as resfile:
        resfile.write(f'{bits*8},{duration},{packets}')
        resfile.flush()
    sys.exit(1)

def server_loop(reverse, udp, sock: socket.socket, buffer_length, duration, zerocopy):
    if not udp:
        conn, _ = sock.accept()
    buffer = [1] * buffer_length
    b = bytes(buffer)
    if zerocopy and reverse:
        zerocopyFile = open('zerocopy_content.txt', 'wb+')
        zerocopyFile.write(bytes(buffer))
        zerocopyFile.flush()
    sent = 0
    received = 0
    firstReceive = True
    packets_received = 0
    packets_sent = 0

    if not reverse:
        while True:
            if not udp:
                data = conn.recv(buffer_length)
                if firstReceive:
                    firstReceive = False
                    start = timeModule.time()
            else: data, _ = sock.recvfrom(buffer_length)
            if not data:
                end = timeModule.time()
                break;
            packets_received += 1
            received += len(data)
    else:
        # reverse mode, TCP is assumed because UDP doesn't work
        end_time = timeModule.time() + duration
        while timeModule.time() < end_time:
            if not zerocopy:
                length = conn.send(b)
            else: 
                # send using socket.sendfile
                length = conn.sendfile(zerocopyFile)
            if firstReceive:
                firstReceive = False
                start = timeModule.time()
            if length:
                sent += length
                packets_sent += 1
            
        end = timeModule.time()
        conn.close()
    if zerocopy and reverse:
        zerocopyFile.close()
    if not reverse:
        return (received,end-start,packets_received)
    return (sent,end-start,packets_sent)
    
def client_loop(reverse, udp, sock: socket.socket, host, port, buffer_length, duration, zerocopy): 
    buffer = [1] * buffer_length
    b = bytes(buffer)
    if zerocopy and not reverse:
        zerocopyFile = open('zerocopy_content.txt', 'wb+')
        zerocopyFile.write(bytes(buffer))
        zerocopyFile.flush()
    sent = 0
    received = 0
    firstReceive = True
    packets_received = 0
    packets_sent = 0
        
    if not udp:
        sock.connect((str(host), port))
    if not reverse:
        end_time = timeModule.time() + duration
        while timeModule.time() < end_time:
            if not udp:
                if not zerocopy:
                    sentBytes = sock.send(b)
                else: 
                    sentBytes =sock.sendfile(zerocopyFile)
            else: sentBytes = sock.sendto(b, (host, port))
            if firstReceive:
                firstReceive = False
                start = timeModule.time()
            if sentBytes > 0:
                packets_sent += 1
                sent += sentBytes
        end = timeModule.time()
    else: 
        while True:
            if not udp:
                data = sock.recv(buffer_length)
                if firstReceive:
                    firstReceive = False
                    start = timeModule.time()
            else: data, _ = sock.recvfrom(buffer_length)
            if not data:
                end = timeModule.time()
                break
            packets_received += 1
            received += len(data)
            
    if not udp and not reverse:
        sock.close()
    if zerocopy and not reverse:
        zerocopyFile.close()
    if not reverse:
        return (sent,end-start,packets_sent)
    return (received,end-start,packets_received)
        
def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv, "p:f:d:c:t:l:uRM:ZJo:",
                                   ["port=" "plot_filename=" "data_filename=" "connections=" "time=" "length=" "udp", "reverse" "set-mss=" "zerocopy" "json" "log-file="])
    except getopt.GetoptError:
        print("Syntax Error.")
        sys.exit(2)

    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET])
    addrsv6 = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6])
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
    zerocopy = False
    json = False
    log_file = False
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--connections"):
            connections = int(arg)
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
        elif opt in ('-Z', '--zerocopy'):
            zerocopy = True
        elif opt in ('-J', '--json'):
            json = True
        elif opt in ('-o', '--log-file'):
            log_file = arg
        
    port = int(port)

    serverpid = start_server(reverse, udp, ip, port, length, connections, duration, mss, zerocopy)
    clientpid = start_client(reverse, udp, ip, port, length, duration, connections, mss, zerocopy)

    try:
        os.waitpid(serverpid, 0)
        os.waitpid(clientpid, 0)
    except ChildProcessError:
        print()
    with open('client-res.txt', 'r') as client_res:
        with open('server-res.txt', 'r') as server_res:
            client_line = client_res.read()
            server_line = server_res.read()
            client_bits,client_duration,client_packets = client_line.split(',')
            server_speed,server_packets = server_line.split(',')
            loss = abs(int(server_packets)-int(client_packets)) / int(client_packets)
            
            download_prefix,download = get_prefix(float(server_speed))
            upload_prefix,upload = get_prefix(float(client_bits)/float(client_duration))
            
            if not json:
                str = f'Download speed achieved is {download} {download_prefix}, upload speed is {upload} {upload_prefix}, packet loss is {loss}'
            else:
                res = {
                    'download': f'{download} {download_prefix}',
                    'upload': f'{upload} {upload_prefix}',
                    'packet_loss': loss
                }
                
                str = jsonModule.dumps(res)
            
            if not log_file:
                print(str)
            else:
                with open(log_file, 'w') as outfile:
                    outfile.write(str)
                
                

if __name__ == "__main__":
    main(sys.argv[1:])