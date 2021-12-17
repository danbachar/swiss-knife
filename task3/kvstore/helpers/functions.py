#!/usr/bin/env python3
import os
import shutil
from contextlib import closing
import socket
import signal
import psutil

def log(msg):
    print("\n")
    print("#" * (12 + len(msg)))
    print("#"*5, msg, "#"*5)
    print("#" * (12 + len(msg)))
    print("\n")

def cloneRocksDB():
    """Clone rocksdb from git"""
    if not os.path.exists("rocksdb"):
        #shutil.rmtree("rocksdb")
        os.system("git clone https://github.com/facebook/rocksdb.git")

def downloadYCSB():
    """Download YCSB from git"""
    if os.path.exists("YCSB"):
        shutil.rmtree("YCSB")
    os.system("curl -O --location https://github.com/brianfrankcooper/YCSB/releases/download/0.17.0/ycsb-0.17.0.tar.gz && tar xfvz ycsb-0.17.0.tar.gz && mv ycsb-0.17.0 YCSB")
    
def cloneYCSB():
    """Clone YCSB from git"""
    if os.path.exists("YCSB"):
        shutil.rmtree("YCSB")
    os.system("git clone http://github.com/brianfrankcooper/YCSB.git")
    
    
# Taken from here https://stackoverflow.com/a/45690594
def find_free_port():
    """Find and return a port that is not taken"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
    
def shutdown_memcached():
    """Kill 'memcached' processes started by user 'teama'"""
    for proc in psutil.process_iter():
        try:
            # Get process name & pid from process object.
            processName = proc.name()
            processID = proc.pid
            processUsername = proc.username()
            if "memcached" in processName and "teama" in processUsername:
                print('killing ', processName , ' PID: ', processID, ' USERNAME: ', processUsername)
                os.kill(processID, signal.SIGINT)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        
def configureMemcachedYCSB(host, port):
    """This will specify to YCSB which interface and port to use for memcache test"""
    if os.path.exists("conf"):
        shutil.rmtree("conf")
    os.mkdir("conf")
    with open("conf/memcacehd.properties", "w") as f:
        f.write(f"memcached.hosts = '{host}:{port}'")