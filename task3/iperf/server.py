#!/usr/bin/env python3

import subprocess
import netifaces as ni
import json
import time
import sys
import numpy as np
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
TYPE ='Type'
PROPERTY ='Property'

class Measurement:
    def __init__(self, speed, prefix, normalizedSpeed, jitter, loss):
        self.speed = speed
        self.normalizedSpeed = normalizedSpeed
        self.prefix = prefix
        self.jitter = jitter
        self.loss = loss
        
def remove_file(filename) -> None: 
    proc = subprocess.Popen(['rm', '-f', filename])
    proc.wait()
    
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

def get_measurement(res_file, udp, reverse) -> Measurement:
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
            if reverse:
                bitsPerSecond = obj['end']['sum_sent']['bits_per_second']
                seconds = obj['end']['sum_sent']['seconds']
            else:   
                bitsPerSecond = obj['end']['sum_received']['bits_per_second']
                seconds = obj['end']['sum_received']['seconds']

        prefix, normalizedSpeed = get_prefix(bitsPerSecond)
        return Measurement(bitsPerSecond, prefix, normalizedSpeed, jitter, loss)
    
def increase_window_size_limit():
    subprocess.Popen(['sudo', 'sysctl', '-w', 'net.core.rmem_max=67108864']) # allow testing with buffers up to 64MB 
    subprocess.Popen(['sudo', 'sysctl', '-w', 'net.core.wmem_max=67108864']) # allow testing with buffers up to 64MB 
    subprocess.Popen(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_rmem="4096 87380 33554432"']) # increase Linux autotuning TCP buffer limit to 32MB
    subprocess.Popen(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_wmem="4096 65536 33554432"']) # increase Linux autotuning TCP buffer limit to 32MB
    subprocess.Popen(['sudo', 'sysctl', '-w', 'net.ipv4.tcp_mtu_probing=1']) # recommended for hosts with jumbo frames enabled

def test_window_size(url, data_filename, plot_filename, port, connections, duration):
    increase_window_size_limit()
    window_sizes = [ 64, 128, 256, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i, open(data_filename+'_parallel.csv', 'a') as p:
        f.write(f'{WINDOW_SIZE},{SPEED}\n')
        f.flush()

        g.write(f'{WINDOW_SIZE},{SPEED}\n')
        g.flush()

        h.write(f'{WINDOW_SIZE},{JITTER}\n')
        h.flush()

        i.write(f'{WINDOW_SIZE},{LOSS}\n')
        i.flush()
        
        p.write(f'{CONNECTIONS},{WINDOW_SIZE},{SPEED}\n')
        p.flush()
        for ws in window_sizes:
            measurement=benchmark(url, port, connections, duration, ws, True, 0, False, False, False)
            measurement_udp=benchmark(url, port, connections, duration, ws, False, 0, False, False, False)
            measurement_parallel=benchmark(url, port, connections, duration, ws, True, 0, False, False, False)
            
            
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
            udp_graph = dg.plot(x=WINDOW_SIZE, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            
            p.write(f'{connections},{ws},{measurement_parallel.speed}\n')
            p.flush()
            dp = pd.read_csv(data_filename+'_parallel.csv')
            dp.plot(x=WINDOW_SIZE, y=SPEED, color='GREEN', label=f'{connections} connections', ax=udp_graph)
            
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
    payload_sizes = [ 0.5 * 128, 128, 128 * 1.5, 2 * 128, 2.5 * 128, 3 * 128, 0.5 * 1460, 1460, 1.5 * 1460, 2 * 1460, 2.5 * 1460,  3 * 1460, 10 * 1460, 20 * 1460]
    remove_file(data_filename)
    remove_file(data_filename+'_udp.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_udp.csv', 'a') as g, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i, open(data_filename+'_parallel.csv', 'a') as p:
        f.write(f'{PAYLOAD_SIZE},{SPEED}\n')
        f.flush()

        g.write(f'{PAYLOAD_SIZE},{SPEED}\n')
        g.flush()
        h.write(f'{PAYLOAD_SIZE},{JITTER}\n')
        h.flush()

        i.write(f'{PAYLOAD_SIZE},{LOSS}\n')
        i.flush()
        
        p.write(f'{CONNECTIONS},{PAYLOAD_SIZE},{SPEED}\n')
        p.flush()
        for ps in payload_sizes:
            measurement=benchmark(url, port, connections, duration, 0, True, ps, False, False, False)
            measurement_udp=benchmark(url, port, connections, duration, 0, False, ps, False, False, False)
            measurement_parallel=benchmark(url, port, connections, duration, 0, True, ps, False, False, False)
            
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
            udp_graph = dg.plot(x=PAYLOAD_SIZE, y=SPEED, color='RED', label='UDP', ax=tcp_graph)
            
            p.write(f'{connections},{ps},{measurement_parallel.speed}\n')
            p.flush()
            dp = pd.read_csv(data_filename+'_parallel.csv')
            dp.plot(x=PAYLOAD_SIZE, y=SPEED, color='RED', label=f'{connections} connections', ax=udp_graph)
            
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
            
def test_parallel(url, data_filename, plot_filename, port, connections, duration):
    remove_file(data_filename)
    with open(data_filename, 'a') as f, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{CONNECTIONS},{SPEED},{TYPE}\n')
        f.flush()
        
        h.flush()
        h.write(f'{CONNECTIONS},{JITTER},{TYPE}\n')

        i.flush()
        i.write(f'{CONNECTIONS},{LOSS},{TYPE}\n')
        for numConnections in range(1, connections+1):
            measurement=benchmark(url, port, numConnections, duration, 0, True, 0, False, False, False)
            measurement_udp=benchmark(url, port, numConnections, duration, 0, False, 0, False, False, False)
                
            print('TCP achieved speed: ', measurement.normalizedSpeed, measurement.prefix, 'parllel connections:', numConnections, 'duration:', duration)
            print('UDP achieved speed: ', measurement_udp.normalizedSpeed, measurement_udp.prefix, 'parllel connections:', numConnections, 'duration:', duration)
            f.write(f'{numConnections},{measurement.speed},TCP\n')
            f.write(f'{numConnections},{measurement_udp.speed},UDP\n')
            f.flush()
            
            h.write(f'{numConnections},{measurement_udp.jitter},UDP\n')
            h.flush()
            
            i.write(f'{numConnections},{measurement_udp.loss},UDP\n')
            i.flush()
        plot_effect_of_prop_on_speed(data_filename, plot_filename, CONNECTIONS)
               
def plot_effect_of_prop_on_speed(data_filename, plot_filename, indexCol):
    labels = ['True', 'False']
    x = np.arange(len(labels))
    
    fig, ax = plt.subplots()
    
    speed_data = pd.read_csv(data_filename)
    speed_data.pivot(index=indexCol, columns=TYPE, values=SPEED).plot(kind='bar') 
    plt.savefig('./plots/' + plot_filename+'.png')
    
    jitter_data = pd.read_csv(data_filename+'_jitter.csv')
    jitter_data.pivot(index=indexCol, columns=TYPE, values=JITTER).plot(kind='bar') 
    plt.savefig('./plots/' + plot_filename+'_jitter.png')
    
    loss_data = pd.read_csv(data_filename+'_loss.csv')
    loss_data.pivot(index=indexCol, columns=TYPE, values=LOSS).plot(kind='bar') 
    plt.savefig('./plots/' + plot_filename+'_loss.png')
        
def test_props(ip, data_filename, plot_filename, port, connections, duration):
    reverse = [ False, True ]
    remove_file(data_filename)
    remove_file(data_filename+'_jitter.csv')
    remove_file(data_filename+'_loss.csv')
    with open(data_filename, 'a') as f, open(data_filename+'_jitter.csv', 'a') as h, open(data_filename+'_loss.csv', 'a') as i:
        f.write(f'{PROPERTY},{SPEED},{TYPE}\n')
        f.flush()
        
        h.flush()
        h.write(f'{PROPERTY},{JITTER},{TYPE}\n')
        
        i.flush()
        i.write(f'{PROPERTY},{LOSS},{TYPE}\n')
        for switch in reverse:
            measurement_reverse=benchmark(ip, port, connections, duration, 0, True, 0, False, False, switch)
            measurement_udp_reverse=benchmark(ip, port, connections, duration, 0, False, 0, False, False, switch)
            measurement_bidirectional=benchmark(ip, port, connections, duration, 0, True, 0, False, switch, False)
            measurement_udp_bidirectional=benchmark(ip, port, connections, duration, 0, False, 0, False, switch, False)
            measurement_zerocopy=benchmark(ip, port, connections, duration, 0, True, 0, switch, False, False)
            measurement_udp_zerocopy=benchmark(ip, port, connections, duration, 0, False, 0, switch, False, False)
                
            f.write(f'{switch},{measurement_reverse.speed},Reverse\n')
            f.write(f'{switch},{measurement_bidirectional.speed},Bidirectional\n')
            f.write(f'{switch},{measurement_zerocopy.speed},Zerocopy\n')
            f.flush()
            
            h.write(f'{switch},{measurement_udp_reverse.jitter},Reverse\n')
            h.write(f'{switch},{measurement_udp_bidirectional.jitter},Bidirectional\n')
            h.write(f'{switch},{measurement_udp_zerocopy.jitter},Zerocopy\n')
            h.flush()
            
            i.write(f'{switch},{measurement_udp_reverse.loss},Reverse\n')
            i.write(f'{switch},{measurement_udp_bidirectional.loss},Bidirectional\n')
            i.write(f'{switch},{measurement_udp_zerocopy.loss},Zerocopy\n')
            i.flush()
        plot_effect_of_prop_on_speed(data_filename, plot_filename, PROPERTY)
    
def benchmark(url, port, connections, duration, window_size, tcp, payload_length, zerocopy, is_bidirectional, is_reverse) -> Measurement:
    remove_file('res.json')
    if tcp:
        print(f'Running iperf on TCP with {duration}s {window_size}K TCP window size')
    else:
        print(f'Running iperf on UDP with {duration}s {window_size}K TCP window size')
    server_pid = start_server(url, port, 'res.json')
    client_pid = start_client(url, port, connections, duration, window_size, not tcp, payload_length, zerocopy, is_bidirectional, is_reverse)        
    
    measurement = Measurement(0, '', 0, 0, 0)
    ret = server_pid.wait()
    if ret == 0 or ret == 1:
        measurement = get_measurement('res.json', not tcp, is_reverse or is_bidirectional)
    else:
        print("something bad happened to the server, ret:", ret)
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
    plot_filename='plot_filename'
    data_filename='./plots/data_filename'
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
            connections = int(arg)
        elif opt in ("-t", "--time"):
            duration = int(arg)
    open_port(port)
    test_window_size(ip, data_filename+'_ws.csv', plot_filename+'_ws', port, connections, duration)
    test_payload_size(ip, data_filename+'_ps.csv', plot_filename+'_ps', port, connections, duration)
    test_props(ip, data_filename, plot_filename, port, connections, duration)
    test_parallel(ip, data_filename+'_parallel.csv', plot_filename+'_parallel', port, connections, duration)
    os.makedirs('./plots', exist_ok=True)
    

if __name__ == "__main__":
    main(sys.argv[1:])
