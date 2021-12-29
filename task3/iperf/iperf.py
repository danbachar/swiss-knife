#!/usr/bin/env python3

import os
import subprocess
import netifaces as ni


PORT = 5201

def start_server(url) -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Starting iperf server...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    pid = os.fork()
    if pid == 0:
        process = subprocess.Popen(['iperf', '-s -p', str(PORT), '-B', url],
                                    stdout=subprocess.PIPE,
                                    universal_newlines=True)

def start_client(url) -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Starting iperf client...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    process = subprocess.Popen(['iperf', '-c -p', str(PORT), '-B', url],
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
    



def open_port() -> None:
    # using fuser to remove blocking process from using determinated ports
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Opening port...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    process = subprocess.Popen(['fuser', '-k', str(PORT)+'/tcp'],
                                stdout=subprocess.PIPE,
                                universal_newlines=True)

    while True:
        output = process.stdout.readline()
        print(output.strip())
        # Do something else
        return_code = process.poll()
        if return_code is not None:
            print('RETURN CODE', return_code)
            # Process has finished, read rest of the output
            for output in process.stdout.readlines():
                print(output.strip())
            break


def nix_build() -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Building Nix environment...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    stream = os.popen('nix-build')
    print(stream.read())



def main() -> None:
    nix_build()
    open_port()
    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6])
    ip = list(filter(lambda ip: "swissknife0" in ip, addrs)).pop()
    URL = f"http://[{ip}]"   
    start_server(URL)
    start_client(URL)
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("fin")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main()
