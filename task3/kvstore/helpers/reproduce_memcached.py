#!/usr/bin/env python3
from shutil import copyfile
from helpers.functions import log, cloneYCSB, find_free_port, shutdown_memcached
from helpers.constants import MIN_TARGET_POW, MAX_TARGET_POW, TARGET_MULTIPLIER, THREAD_COUNT_OPTION, RESULT_FOLDER
import os

log("CLONE YCSB FOR MEMCACHED")
cloneYCSB()

log("BUILD YCSB FOR MEMCACHED")
os.system("cd YCSB && mvn -pl site.ycsb:memcached-binding -am clean package && cd ../")

log("START MEMCACHED DAEMON SERVER")
PORT = find_free_port()
# Use IPv4 localhost as YCSB apparently does not support IPv6
HOST = '127.0.0.1'

# start memcached server
os.popen(f"memcached -d -p {PORT} -l {HOST}")

# Add custom workload 'g' - write only
copyfile("custom_workload", "YCSB/workloads/workloadg")

# load and run benchmark on rocksdb instance
for workload in 'abcdefg':
    
    for i in range(MIN_TARGET_POW, MAX_TARGET_POW):
        target = pow(2, i)
        # For workload g the databases don't reach this throughput anyway
        if workload == 'g' and i > 15:
            continue
        # run the benchmark for each target
        log(f"RUN BENCHMARKS ON MEMCACHED. WORKLOAD {workload}. TARGET {target} OPS/SEC.")
        os.system(f"""
                cd YCSB/ ;
                ./bin/ycsb.sh load memcached -P workloads/workload{workload} {THREAD_COUNT_OPTION} -target {target} -p "memcached.hosts={HOST}:{PORT}" -p operationcount={TARGET_MULTIPLIER*target if workload != 'g' else 5000} -p recordcount=10000 > ../{RESULT_FOLDER}/memcached/workload_{workload}_target_{target}.txt;
                ./bin/ycsb.sh run memcached -s -P workloads/workload{workload} {THREAD_COUNT_OPTION} -target {target} -p "memcached.hosts={HOST}:{PORT}" -p operationcount={TARGET_MULTIPLIER*target if workload != 'g' else 5000} -p recordcount=10000 > ../{RESULT_FOLDER}/memcached/workload_{workload}_target_{target}.txt;
                cd ../ ;
                """)

log("KILL MEMCACHED PROCESSES")
# shutdown memcached server started by teama
shutdown_memcached()