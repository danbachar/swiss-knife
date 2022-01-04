#!/usr/bin/env python3

import subprocess
import netifaces as ni
import json
import time
import sys
import numpy
import os
import getopt
import matplotlib.pyplot as plt
import pandas as pd

PORT = 5201
SPEED = 'Speed'
PREFIX = 'Prefix'
CONNECTIONS = 'Connections'
DURATION = 'Duration'
WINDOW_SIZE = 'TCP Window size'
PAYLOAD_SIZE = 'Payload size'
JITTER = 'Jitter ms'
LOSS = 'Packet loss'
ZEROCOPY = 'Zerocopy'
BIDIRECTIONAL = 'Bidirectional'
REVERSE = 'Reverse'

class Measurement:
    def __init__(self, speed, prefix, normalizedSpeed, jitter, loss):
        self.speed = speed
        self.normalizedSpeed = normalizedSpeed
        self.prefix = prefix
        self.jitter = jitter
        self.loss = loss
        
def remove_file(filename) -> None: 
    print(f'Removing {filename}...')
    proc = subprocess.Popen(['rm', '-f', filename])
    proc.wait()
    print(f'{filename} removed.')
    
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
    
def start_server(url, port, res_file): 
    return subprocess.Popen(['iperf', '-1', '-s', '-B', url, '-J', '--logfile', res_file, '-p', str(port), '--idle-timeout', '10'], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE, 
                            universal_newlines=True)
    
def start_client(ip, port, clients, duration, window_size, udp, payload_length, zerocopy, bidirectional, reverse) -> None:
    time.sleep(3)
    
    arr = ['iperf', '-c', ip, '-p', str(port), '-t', str(duration), '-P', str(clients)]
    if udp:
        arr.append('-u')
        arr.append('-b')
        arr.append('100G')
    if window_size != 0:
        arr.append('-w')
        arr.append(str(window_size)+'K')
    if payload_length != 0:
        arr.append('-l')
        arr.append(str(payload_length))
    if zerocopy:
        arr.append('-Z')
    if bidirectional:
        arr.append('--bidir')
    if reverse:
        arr.append('-R')
    subprocess.Popen(arr, universal_newlines=True).wait()

def get_measurement(res_file, udp) -> Measurement:
    with open(res_file, 'r') as file:
        data = file.read().replace('\n', '')
        obj = json.loads(data)
        bitsPerSecond = 0
        seconds=0
        jitter=0
        loss=0
        if udp:
            sum=0
            for stream in obj['intervals']:
                sum += stream['sum']['bits_per_second']
                seconds += stream['sum']['seconds']
            bitsPerSecond = sum/seconds
            jitter = obj['end']['sum']['jitter_ms']
            loss = obj['end']['sum']['lost_percent']
        else:
            bitsPerSecond = obj['end']['sum_received']['bits_per_second']
            seconds = obj['end']['sum_received']['seconds']

        prefix, normalizedSpeed = get_prefix(bitsPerSecond)
        return Measurement(bitsPerSecond, prefix, normalizedSpeed, jitter, loss)
    
def test_window_size(url, data_filename, plot_filename, port, connections, duration):
    window_sizes = [ 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096 ]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{WINDOW_SIZE},{SPEED}\n')
        g.write(f'{WINDOW_SIZE},{SPEED}\n')
        h.write(f'{WINDOW_SIZE},{JITTER}\n')
        i.write(f'{WINDOW_SIZE},{LOSS}\n')
        f.flush()
        g.flush()
        h.flush()
        i.flush()
        for ws in window_sizes:
            measurement=benchmark(url, port, connections, duration, ws, True, 0, False, False, False)
            measurement_udp=benchmark(url, port, connections, duration, ws, False, 0, False, False, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'window size:', ws, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'window size:', ws, 'duration:', duration)
            f.write(f'{ws},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=WINDOW_SIZE, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{ws},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=WINDOW_SIZE, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{ws},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=WINDOW_SIZE, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{ws},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=WINDOW_SIZE, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')        

def test_payload_size(url, data_filename, plot_filename, port, connections, duration):
    payload_sizes = [ 0.5 * 128, 128, 128 * 1.5, 2 * 128, 2.5 * 128, 3 * 128, 0.5 * 1460, 1460, 1.5 * 1460, 2 * 1460, 2.5 * 1460,  3 * 1460]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{PAYLOAD_SIZE},{SPEED}\n')
        f.flush()
        
        g.write(f'{PAYLOAD_SIZE},{SPEED}\n')
        g.flush()
        
        h.flush()
        h.write(f'{PAYLOAD_SIZE},{JITTER}\n')

        i.flush()
        i.write(f'{PAYLOAD_SIZE},{LOSS}\n')
        for ps in payload_sizes:
            measurement=benchmark(url, port, connections, duration, 0, True, ps, False, False, False)
            measurement_udp=benchmark(url, port, connections, duration, 0, False, ps, False, False, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'payload size:', ps, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'payload size:', ps, 'duration:', duration)
            f.write(f'{ps},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=PAYLOAD_SIZE, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{ps},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=PAYLOAD_SIZE, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{ps},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=PAYLOAD_SIZE, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{ps},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=PAYLOAD_SIZE, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')        
            
def test_zerocopy(url, data_filename, plot_filename, port, connections, duration):
    zerocopy = [ False, True ]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{ZEROCOPY},{SPEED}\n')
        f.flush()
        
        g.write(f'{ZEROCOPY},{SPEED}\n')
        g.flush()
        
        h.flush()
        h.write(f'{ZEROCOPY},{JITTER}\n')

        i.flush()
        i.write(f'{ZEROCOPY},{LOSS}\n')
        for zc in zerocopy:
            measurement=benchmark(url, port, connections, duration, 0, True, 0, zc, False, False)
            measurement_udp=benchmark(url, port, connections, duration, 0, False, 0, zc, False, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'zerocopy:', zc, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'zerocopy:', zc, 'duration:', duration)
            f.write(f'{zc},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=ZEROCOPY, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{zc},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=ZEROCOPY, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{zc},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=ZEROCOPY, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{zc},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=ZEROCOPY, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')
            
def test_parallel(url, data_filename, plot_filename, port, connections, duration):
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{CONNECTIONS},{SPEED}\n')
        f.flush()
        
        g.write(f'{CONNECTIONS},{SPEED}\n')
        g.flush()
        
        h.flush()
        h.write(f'{CONNECTIONS},{JITTER}\n')

        i.flush()
        i.write(f'{CONNECTIONS},{LOSS}\n')
        for numConnections in range(1, connections+1):
            measurement=benchmark(url, port, numConnections, duration, 0, True, 0, False, False, False)
            measurement_udp=benchmark(url, port, numConnections, duration, 0, False, 0, False, False, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'parllel connections:', numConnections, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'parllel connections:', numConnections, 'duration:', duration)
            f.write(f'{numConnections},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=CONNECTIONS, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{numConnections},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=CONNECTIONS, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{numConnections},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=CONNECTIONS, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{numConnections},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=CONNECTIONS, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')
    
def test_bidirectional(url, data_filename, plot_filename, port, connections, duration):
    bidirectional = [ False, True ]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{BIDIRECTIONAL},{SPEED}\n')
        f.flush()
        
        g.write(f'{BIDIRECTIONAL},{SPEED}\n')
        g.flush()
        
        h.flush()
        h.write(f'{BIDIRECTIONAL},{JITTER}\n')

        i.flush()
        i.write(f'{BIDIRECTIONAL},{LOSS}\n')
        for switch in bidirectional:
            measurement=benchmark(url, port, connections, duration, 0, True, 0, False, switch, False)
            measurement_udp=benchmark(url, port, connections, duration, 0, False, 0, False, switch, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'bidirectional:', switch, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'bidirectional:', switch, 'duration:', duration)
            f.write(f'{switch},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=BIDIRECTIONAL, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{switch},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=BIDIRECTIONAL, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{switch},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=BIDIRECTIONAL, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{switch},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=BIDIRECTIONAL, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')

def test_reverse(url, data_filename, plot_filename, port, connections, duration):
    reverse = [ False, True ]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{REVERSE},{SPEED}\n')
        f.flush()
        
        g.write(f'{REVERSE},{SPEED}\n')
        g.flush()
        
        h.flush()
        h.write(f'{REVERSE},{JITTER}\n')

        i.flush()
        i.write(f'{REVERSE},{LOSS}\n')
        for switch in reverse:
            measurement=benchmark(url, port, connections, duration, 0, True, 0, False, False, switch)
            measurement_udp=benchmark(url, port, connections, duration, 0, False, 0, False, False, switch)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'reverse mode:', switch, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'reverse mode:', switch, 'duration:', duration)
            f.write(f'{switch},{measurement.speed}\n')
            f.flush()
            df = pd.read_csv(data_filename)
            tcp_graph = df.plot(x=REVERSE, y=SPEED, color='BLUE', label='TCP')
            tcp_graph.set_ylabel("Speed: bits/second")
            
            g.write(f'{switch},{measurement_udp.speed}\n')
            g.flush()
            dg = pd.read_csv(data_filename+'_udp.csv')
            dg.plot(x=REVERSE, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            plt.savefig('./plots/' + plot_filename+'.png')
            
            h.write(f'{switch},{measurement_udp.jitter}\n')
            h.flush()
            dh = pd.read_csv(data_filename+'_jitter.csv')
            jitter_graph = dh.plot(x=REVERSE, y=JITTER)
            jitter_graph.set_ylabel("Jitter: ms")
            plt.savefig('./plots/' + plot_filename+'_jitter.png')
            
            i.write(f'{switch},{measurement_udp.loss}\n')
            i.flush()
            di = pd.read_csv(data_filename+'_loss.csv')
            loss_graph = di.plot(x=REVERSE, y=LOSS)
            loss_graph.set_ylabel("Packet loss")
        
            plt.savefig('./plots/' + plot_filename+'_loss.png')
    
def benchmark(url, port, connections, duration, window_size, tcp, payload_length, zerocopy, is_bidirectional, is_reverse) -> Measurement:
    remove_file('res.json')
    if tcp:
        print(f'Running iperf on TCP with {duration}s {window_size}K TCP window size')
    else:
        print(f'Running iperf on UDP with {duration}s {window_size}K TCP window size')
    server_pid = start_server(url, port, 'res.json')
    client_pid = start_client(url, port, connections, duration, window_size, not tcp, payload_length, zerocopy, is_bidirectional, is_reverse)        
    
    measurement = Measurement(0, '', 0, 0, 0)
    if server_pid.wait() == 0:
        measurement = get_measurement('res.json', not tcp)
    else:
        print("something bad happened to the server")
    return measurement
        
def open_port(port) -> None:
    # using fuser to remove blocking process from using determinated ports    
    process = subprocess.Popen(['fuser', '-k', f'{port}/tcp'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True)
    while True:
            output = process.stdout.readline()
            print(output.strip())
            # Do something else
            return_code = process.poll()
            if return_code is not None:
                # Process has finished, read rest of the output
                for output in process.stdout.readlines():
                    print(output.strip())
                break
        

def main(argv) -> None:
    try:
        opts, args = getopt.getopt(argv, "p:f:d:c:t:",
                                   ["port=" "plot_filename=" "data_filename=" "connections=" "time="])
    except getopt.GetoptError:
        print("Syntax Error.")
        sys.exit(2)

    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6])
    ip = list(filter(lambda ip: "swissknife0" in ip, addrs)).pop()
    print("ip: ", ip)
    global port
    global plot_filename
    global data_filename
    port = "5201"
    connections = 5
    duration = 1
    for opt, arg in opts:
        if opt in ("-p", "--port"):
            port = arg
        elif opt in ("-f", "--filename_plot"):
            plot_filename = arg
        elif opt in ("-d", "--filename_data"):
            data_filename = './plots/' + arg
        elif opt in ("-c", "--connections"):
            print("connections is ", opt, arg)
            connections = int(arg)
        elif opt in ("-t", "--time"):
            print("time is ", opt, arg)
            duration = int(arg)
    open_port(port)
    test_window_size(ip, data_filename+'_ws.csv', plot_filename+'_ws', port, connections, duration)
    test_payload_size(ip, data_filename+'_ps.csv', plot_filename+'_ps', port, connections, duration)
    test_zerocopy(ip, data_filename+'_zc.csv', plot_filename+'_zc', port, connections, duration)
    test_parallel(ip, data_filename+'_parallel.csv', plot_filename+'_parallel', port, connections, duration)
    test_bidirectional(ip, data_filename+'_bidirectional.csv', plot_filename+'_bidirectional', port, connections, duration)
    test_reverse(ip, data_filename+'_reverse.csv', plot_filename+'_reverse', port, connections, duration)
    os.makedirs('./plots', exist_ok=True)
    
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("fin")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main(sys.argv[1:])
