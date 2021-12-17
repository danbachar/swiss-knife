#!/usr/bin/env python3
from shutil import copyfile
from helpers.functions import log, cloneRocksDB, downloadYCSB
from helpers.constants import MIN_TARGET_POW, MAX_TARGET_POW, ROCKSDB_PATH, TARGET_MULTIPLIER, THREAD_COUNT_OPTION, RESULT_FOLDER
import os

# TODO uncomment!!!
log("CLONE AND BUILD ROCKSDB. MAY TAKE A WHILE. PLEASE BE PATIENT.")
cloneRocksDB()
# build static_lib
os.system("cd rocksdb && make static_lib && cd ../")
# build shared_lib
os.system("cd rocksdb && make shared_lib && cd ../ ")
log("DOWNLOAD YCSB FOR ROCKSDB")
downloadYCSB()

log("CREATE A ROCKSDB INSTANCE")
# build initRocksDB
os.system("make")
# init a rocksdb instance for testing
os.system(f'./bin/initRocksDB {ROCKSDB_PATH}')

# Add custom workload 'g' - write only
copyfile("custom_workload", "YCSB/workloads/workloadg")

# load and run benchmark on rocksdb instance
for workload in 'g':
    
    for i in range(MIN_TARGET_POW, MAX_TARGET_POW):
        target = pow(2, i)
        # run the benchmark for each target
        log(f"RUN BENCHMARKS ON ROCKSDB. WORKLOAD {workload}. TARGET {target} OPS/SEC.")
        os.system(f"""
                cd YCSB/ ;
                ./bin/ycsb.sh load rocksdb -P workloads/workload{workload} -target {target} {THREAD_COUNT_OPTION} -p rocksdb.dir="{ROCKSDB_PATH}" -p operationcount={TARGET_MULTIPLIER*target if workload != 'g' else 5000} -p recordcount=1000 > ../{RESULT_FOLDER}/rocksdb/workload_{workload}_target_{target}.txt;
                ./bin/ycsb.sh run rocksdb -s -P workloads/workload{workload} -target {target} {THREAD_COUNT_OPTION} -p rocksdb.dir="{ROCKSDB_PATH}" -p operationcount={TARGET_MULTIPLIER*target if workload != 'g' else 5000} -p recordcount=1000 > ../{RESULT_FOLDER}/rocksdb/workload_{workload}_target_{target}.txt;
                cd ../ ;
                """)
        