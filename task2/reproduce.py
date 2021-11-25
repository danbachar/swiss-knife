#!/usr/bin/env python3

import os
import subprocess

PORTS = [64000, 64001, 64002, 64003, 64004, 64005]
SERVERS = ["server", "server_epoll", "server_epoll_multitask",
           "server_select", "server_thread", "server_uring"]


def benchmarks() -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Performing benchmarks... (can take a while)")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    # we use subprocess as we need better handling of readlines
    for i in range(0, 6):
        print("++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Benchmarking " + SERVERS[i] + " implementation")
        print("++++++++++++++++++++++++++++++++++++++++++++++++")
        process = subprocess.Popen(['python', './benchmark/benchmark.py', '-p', str(PORTS[i]), '-f', str(SERVERS[i]), '-d ', str(SERVERS[i])],
                                   stdout=subprocess.PIPE,
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


def start_servers() -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("starting Servers...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    for server in SERVERS:
        stream = os.popen('./result/bin/' + server + " &")
        print(server + " started")


def open_ports() -> None:
    # using fuser to remove blocking process from using determinated ports
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Opening ports...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    for port in PORTS:
        process = subprocess.Popen(['fuser', '-k', str(port)+'/tcp'],
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
    open_ports()
    start_servers()
    benchmarks()


if __name__ == "__main__":
    main()
