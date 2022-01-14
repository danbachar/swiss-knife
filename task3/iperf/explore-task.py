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
import ctypes
import pandas as pd
import matplotlib.pyplot as plt
from server import CONNECTIONS, SPEED, TYPE, remove_file

# Adapted from https://github.com/ModioAB/snippets/blob/master/src/tcp_info.py
class TcpInfo(ctypes.Structure):
    """TCP_INFO struct in linux 4.2
    see /usr/include/linux/tcp.h for details"""

    __u8 = ctypes.c_uint8
    __u32 = ctypes.c_uint32
    __u64 = ctypes.c_uint64

    _fields_ = [
        ("tcpi_state", __u8),
        ("tcpi_ca_state", __u8),
        ("tcpi_retransmits", __u8),
        ("tcpi_probes", __u8),
        ("tcpi_backoff", __u8),
        ("tcpi_options", __u8),
        ("tcpi_snd_wscale", __u8, 4), ("tcpi_rcv_wscale", __u8, 4),

        ("tcpi_rto", __u32),
        ("tcpi_ato", __u32),
        ("tcpi_snd_mss", __u32),
        ("tcpi_rcv_mss", __u32),

        ("tcpi_unacked", __u32),
        ("tcpi_sacked", __u32),
        ("tcpi_lost", __u32),
        ("tcpi_retrans", __u32),
        ("tcpi_fackets", __u32),

        # Times
        ("tcpi_last_data_sent", __u32),
        ("tcpi_last_ack_sent", __u32),
        ("tcpi_last_data_recv", __u32),
        ("tcpi_last_ack_recv", __u32),
        # Metrics
        ("tcpi_pmtu", __u32),
        ("tcpi_rcv_ssthresh", __u32),
        ("tcpi_rtt", __u32),
        ("tcpi_rttvar", __u32),
        ("tcpi_snd_ssthresh", __u32),
        ("tcpi_snd_cwnd", __u32),
        ("tcpi_advmss", __u32),
        ("tcpi_reordering", __u32),

        ("tcpi_rcv_rtt", __u32),
        ("tcpi_rcv_space", __u32),

        ("tcpi_total_retrans", __u32),

        ("tcpi_pacing_rate", __u64),
        ("tcpi_max_pacing_rate", __u64),

        # RFC4898 tcpEStatsAppHCThruOctetsAcked
        ("tcpi_bytes_acked", __u64),
        # RFC4898 tcpEStatsAppHCThruOctetsReceived
        ("tcpi_bytes_received", __u64),
        # RFC4898 tcpEStatsPerfSegsOut
        ("tcpi_segs_out", __u32),
        # RFC4898 tcpEStatsPerfSegsIn
        ("tcpi_segs_in", __u32),
    ]
    del __u8, __u32, __u64

    def __repr__(self):
        keyval = ["{}={!r}".format(x[0], getattr(self, x[0]))
                  for x in self._fields_]
        fields = ", ".join(keyval)
        return "{}({})".format(self.__class__.__name__, fields)

    @classmethod
    def from_socket(cls, sock):
        """Takes a socket, and attempts to get TCP_INFO stats on it. Returns a
        TcpInfo struct"""
        # http://linuxgazette.net/136/pfeiffer.html
        padsize = ctypes.sizeof(TcpInfo)
        data = sock.getsockopt(socket.SOL_TCP, socket.TCP_INFO, padsize)
        # On older kernels, we get fewer bytes, pad with null to fit
        padded = data.ljust(padsize, b'\0')
        return cls.from_buffer_copy(padded)

# Adapted Worker+ThreadPool from https://stackoverflow.com/a/7257510
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks, retVal = 0):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()
        self.retVal = retVal

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
        
        retrans = 0
        cnt = 0
        avg_jitter=0
        for worker in self.workers:
            cnt+=1
            if type(worker.retVal) is tuple:
                sum += worker.retVal[0]
                packets += worker.retVal[2]
                retrans = max(retrans, worker.retVal[3])
                avg_jitter += worker.retVal[4]
        
        return (sum, packets, retrans, avg_jitter/cnt)

class Measurement:
    def __init__(self, server_speed, client_speed, packet_loss, server_retrans, client_retrans, jitter):
        self.server_speed = server_speed
        self.client_speed = client_speed
        self.packet_loss = packet_loss
        self.server_retrans = server_retrans
        self.client_retrans = client_retrans
        self.jitter = jitter


    
PORT = 5201        # Port to listen on (non-privileged ports are > 1023)

def get_prefix(speed):
    spd = float(speed)
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

def getTCPInfo(s):
    return TcpInfo.from_socket(s)
        
def create_client_socket_and_connect(reverse, ip, port, buffer_length, duration, mss, zerocopy, window_size):
    s = create_socket(ip, buffer_length, mss, window_size)
    return client_loop(reverse, s, ip, port, buffer_length, duration, zerocopy)
    
def create_socket(ip, buffer_length, mss, window_size) -> socket.socket:
    if isinstance(ip, ipaddress.IPv4Address):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif isinstance(ip, ipaddress.IPv6Address):
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, bytes('swissknife0'.encode()))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_length)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_length)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    if mss:
        s.setsockopt(socket.SOL_SOCKET, socket.TCP_MAXSEG, mss)
    if window_size:
        s.setsockopt(socket.SOL_SOCKET, socket.TCP_WINDOW_CLAMP, window_size)

        
    return s

def start_server(reverse, host, port, buffer_length, connections, duration, mss, zerocopy, window_size):
    childpid = os.fork()
    if childpid != 0:
        return childpid
    ip = ipaddress.ip_address(host)
    
    s = create_socket(ip, buffer_length, mss, window_size)
    s.bind((str(ip), port))
    s.listen()
    
    avg_jitter=0
    speed = 0
    if connections > 1:
        pool = ThreadPool(connections)
        for _ in range(connections):
            pool.add_task(server_loop, reverse, s, buffer_length, duration, zerocopy)
        begin = timeModule.time()
        (bits, packets, retrans, avg_jitter) = pool.wait_completion_and_return_sum_and_packets()
        duration = timeModule.time() - begin
    else:
        (bits,duration,packets,retrans, avg_jitter) = server_loop(reverse, s, buffer_length, duration, zerocopy)
    speed = (bits/duration)
    speed *= 8 # everything is bytes
    
    with open('server-res.txt', 'w') as resfile:
        resfile.write(f'{speed},{packets},{retrans},{avg_jitter}')
        resfile.flush()
    
    sys.exit(1)
    
def start_client(reverse, host, port, buffer_length, duration, connections, mss, zerocopy, window_size) -> int:
    childpid = os.fork()
    if childpid != 0:
        return childpid
    timeModule.sleep(1)
    ip = ipaddress.ip_address(host)
    if connections > 1:
        pool = ThreadPool(connections)
        for _ in range(connections):
            pool.add_task(create_client_socket_and_connect, reverse, ip, port, buffer_length, duration, mss, zerocopy, window_size)
        begin = timeModule.time()
        (bits, packets, retrans, avg_jitter) = pool.wait_completion_and_return_sum_and_packets()
        duration = timeModule.time() - begin
    else:
        s = create_socket(ip, buffer_length, mss, window_size)
        (bits, duration, packets, retrans, avg_jitter) = client_loop(reverse, s, host, port, buffer_length, duration, zerocopy)
    with open('client-res.txt', 'w') as resfile:
        resfile.write(f'{bits*8},{duration},{packets},{retrans},{avg_jitter}')
        resfile.flush()
        
    sys.exit(1)

def server_loop(reverse, sock: socket.socket, buffer_length, duration, zerocopy):
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
    jitters = []

    if not reverse:
        while True:
            data = conn.recv(buffer_length)
            if firstReceive:
                firstReceive = False
                start = timeModule.time()
            if not data:
                end = timeModule.time()
                break;
            packets_received += 1
            received += len(data)
    else:
        # reverse mode
        previous = timeModule.time()
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
                now = timeModule.time()
                sent += length
                packets_sent += 1
                jitters.append(now-previous)
                previous = now
            
        end = timeModule.time()
        conn.close()
    if zerocopy and reverse:
        zerocopyFile.close()
    if not reverse:
        return (received,end-start,packets_received,getTCPInfo(conn).tcpi_total_retrans, 0)
    return (sent,end-start,packets_sent,getTCPInfo(sock).tcpi_total_retrans, sum(jitters)/len(jitters))
    
def client_loop(reverse, sock: socket.socket, host, port, buffer_length, duration, zerocopy): 
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
    jitters = []
        
    sock.connect((str(host), port))
    if not reverse:
        previous = timeModule.time()
        end_time = timeModule.time() + duration
        while timeModule.time() < end_time:
            if not zerocopy:
                sentBytes = sock.send(b)
            else: 
                sentBytes =sock.sendfile(zerocopyFile)
            if firstReceive:
                firstReceive = False
                start = timeModule.time()
            if sentBytes > 0:
                packets_sent += 1
                sent += sentBytes
                now = timeModule.time()
                jitters.append(now-previous)
                previous = now
        end = timeModule.time()
    else: 
        while True:
            data = sock.recv(buffer_length)
            if firstReceive:
                firstReceive = False
                start = timeModule.time()
            if not data:
                end = timeModule.time()
                break
            packets_received += 1
            received += len(data)
    retrans = getTCPInfo(sock).tcpi_total_retrans
    if not reverse:
        sock.close()
        if zerocopy:
            zerocopyFile.close()
        return (sent,end-start,packets_sent, retrans, sum(jitters)/len(jitters))
    return (received,end-start,packets_received, retrans, 0)

def benchmark(reverse, ip, port, length, connections, duration, mss, zerocopy, ws):
    serverpid = start_server(reverse, ip, port, length, connections, duration, mss, zerocopy, ws)
    clientpid = start_client(reverse, ip, port, length, duration, connections, mss, zerocopy, ws)

    try:
        os.waitpid(serverpid, 0)
        os.waitpid(clientpid, 0)
    except ChildProcessError:
        print()
    with open('client-res.txt', 'r') as client_res:
        with open('server-res.txt', 'r') as server_res:
            client_line = client_res.read()
            server_line = server_res.read()
            client_bits,client_duration,client_packets,client_retrans,client_jitter = client_line.split(',')
            server_speed,server_packets,server_retrans,server_jitter = server_line.split(',')
            loss = abs(int(server_packets)-int(client_packets)) / int(client_packets)
            client_speed = float(client_bits)/float(client_duration)
            
            jitter = max(server_jitter, client_jitter) # one of them has to be 0, other has value, dependant on reverse mode
            return Measurement(server_speed, client_speed, loss, server_retrans, client_retrans, jitter)
        
def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv, "p:f:d:c:t:l:RM:ZJo:w:x",
                                   ["port=" "plot_filename=" "data_filename=" "connections=" "time=" "length=" "reverse" "set-mss=" "zerocopy" "json" "log-file=" "window-size=" "export"])
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
    length=128 * 1000 # 128 KB
    reverse = False
    mss = 0
    zerocopy = False
    json = False
    log_file = False
    ws = 0
    export = False
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = arg
        elif opt in ("-c", "--connections"):
            connections = int(arg)
        elif opt in ("-t", "--time"):
            duration = int(arg)
        elif opt in ("-l", "--length"):
            length = int(arg)
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
        elif opt in ('-w', '--window-size'):
            ws = int(arg)
        elif opt in ('-x', '--export'):
            export = True
        
    port = int(port)
    if not export:
        result = benchmark(reverse, ip, port, length, connections, duration, mss, zerocopy, ws)
        server_prefix,server = get_prefix(result.server_speed)
        client_prefix,client = get_prefix(result.client_speed)
        if not json:
                    str = f'Server speed achieved is {server} {server_prefix}, client speed is {client} {client_prefix}, packet loss is {result.packet_loss}, total TCP server packet retransmissions is {result.server_retrans}, client packet retransmissions is {result.client_retrans}, average jitter is {result.jitter} ms'
        else:
            res = {
                'server': result.server_speed,
                'client': result.client_speed,
                'duration': duration,
                'packet_loss': result.loss,
                'server_tcp_total_retransmissions': result.server_retrans,
                'client_tcp_total_retransmissions': result.client_retrans,
                'jitter': result.jitter
            }
            
            str = jsonModule.dumps(res)
        
        if not log_file:
            print(str)
        else:
            with open(log_file, 'w') as outfile:
                outfile.write(str)
    else:
        with open('explore-task-server.csv', 'w') as server_csv, open('explore-task-client.csv', 'w') as client_csv:
            server_csv.write(f'{CONNECTIONS},{SPEED}\n')
            server_csv.flush()
            
            client_csv.write(f'{CONNECTIONS},{SPEED}\n')
            client_csv.flush()
            
            for conn in [1, 2, 3, 5, 10, 20, 50, 100]:
                result = benchmark(False, ip, port, length, conn, duration, False, False, False)
                
                server_csv.write(f'{conn},{result.server_speed}\n')
                server_csv.flush()

                client_csv.write(f'{conn},{result.client_speed}\n')
                client_csv.flush()
                
            server_speed_data = pd.read_csv('explore-task-server.csv')
            server_speed_graph = server_speed_data.plot(x=CONNECTIONS, y=SPEED, color='BLUE', label='SERVER')
            server_speed_graph.set_ylabel('Speed: bits/s')
            
            client_speed_data = pd.read_csv('explore-task-client.csv')
            client_speed_data.plot(x=CONNECTIONS, y=SPEED, color='RED', label='CLIENT', ax=server_speed_graph)
            plt.savefig('./plots/explore-task.png')

if __name__ == "__main__":
    main(sys.argv[1:])