#!/usr/bin/env python3
import os
import random
import string
import shutil
from contextlib import closing
import socket
import signal
import psutil

RND = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
ROCKSDB_PATH = f'/tmp/teama_rocksdb_benchmark_db_{RND}'

def log(msg):
    print("\n")
    print("#" * (12 + len(msg)))
    print("#"*5, msg, "#"*5)
    print("#" * (12 + len(msg)))
    print("\n")

def cloneRocksDB():
    """Clone rocksdb from git. Remove first if already exist."""
    if not os.path.exists("rocksdb"):
        # shutil.rmtree("rocksdb")
        os.system("git clone https://github.com/facebook/rocksdb.git")

def cloneYCSB():
    """Clone YCSB from git. Remove first if already exist."""
    if os.path.exists("YCSB"):
        shutil.rmtree("YCSB")
    # os.system("git clone http://github.com/brianfrankcooper/YCSB.git")
    os.system("curl -O --location https://github.com/brianfrankcooper/YCSB/releases/download/0.17.0/ycsb-0.17.0.tar.gz && tar xfvz ycsb-0.17.0.tar.gz && mv ycsb-0.17.0 YCSB")
    
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
    
log("CLONE AND BUILD ROCKSDB. MAY TAKE A WHILE. PLEASE BE PATIENT.")
cloneRocksDB()
os.system("cd rocksdb && make static_lib && make shared_lib && cd ../ ")
log("CLONE YCSB")
cloneYCSB()

log("CREATE A ROCKSDB INSTANCE")
# build initRocksDB
os.system("make")
# init a rocksdb instance for testing
os.system(f'./initRocksDB {ROCKSDB_PATH}')

log("RUN BENCHMARKS ON ROCKSDB")
# run benchmark on rocksdb instance
os.system(f'cd YCSB/ && ./bin/ycsb.sh load rocksdb -s -P workloads/workloada -p rocksdb.dir="{ROCKSDB_PATH}" -p recordcount=500000 -threads 16 && cd ../')

log("START MEMCACHED SERVER")
PORT = find_free_port()

# start memcached server
os.popen(f"memcached -d -p {PORT}")

log("BUILD YCSB FOR MEMCACHED")
os.system("cd YCSB && mvn -pl site.ycsb:memcached-binding -am clean package && cd ../")

log("RUN BENCHMARKS ON MEMCACHED")

log("KILL MEMCACHED PROCESSES")
# shutdown memcached server started by teama
shutdown_memcached()