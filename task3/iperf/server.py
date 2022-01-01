#!/usr/bin/env python3

import subprocess
import netifaces as ni
import json
import time

PORT = 5201

def start_server(url) -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Starting iperf server...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    process = subprocess.Popen(['iperf', '-1', '-s', '-B', url, '-J', '--logfile', 'res.json'])
    time.sleep(20) # ugly solution to wait for client to connenct
    with open('res.json', 'r') as file:
        data = file.read().replace('\n', '')
        obj = json.loads(data)
        bitsPerSecond = obj['end']['sum_received']['bits_per_second']
        seconds = obj['end']['sum_received']['seconds']
        speed = bitsPerSecond / seconds
        orderOfMagnitude = 0
        while speed > 1000:
            orderOfMagnitude += 3
            speed /= 1000
        prefix = ''
        if orderOfMagnitude == 3:
            prefix = 'Kbits'
        if orderOfMagnitude == 6:
            prefix = 'Mbits'
        if orderOfMagnitude == 9:
            prefix = 'Gbits'
        if orderOfMagnitude == 12:
            prefix = 'Tbits'
        if orderOfMagnitude == 15:
            prefix = 'holybits'
        print("Test finished, speed achieved is ", speed, prefix, '/sec')
    

def open_port() -> None:
    # using fuser to remove blocking process from using determinated ports
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Opening port...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    process = subprocess.Popen(['rm', 'res.json'],
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
    
    process = subprocess.Popen(['fuser', '-k', '5201/tcp'],
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
        

def main() -> None:
    open_port()
    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6])
    ip = list(filter(lambda ip: "swissknife0" in ip, addrs)).pop()
    start_server(ip)
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("fin")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main()
