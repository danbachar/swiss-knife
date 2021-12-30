#!/usr/bin/env python3

import os
import subprocess
import netifaces as ni


PORT = 5201

def start_client(ip) -> None:
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("Starting iperf client...")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    subprocess.Popen(['iperf', '-c', ip, '-p', str(PORT)],
                                universal_newlines=True).wait()

def main() -> None:
    addrs = map(lambda ip: ip["addr"], ni.ifaddresses('swissknife0')[ni.AF_INET6])
    ip = list(filter(lambda ip: "swissknife0" in ip, addrs)).pop()
    start_client(ip)
    print("++++++++++++++++++++++++++++++++++++++++++++++++")
    print("fin")
    print("++++++++++++++++++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main()
