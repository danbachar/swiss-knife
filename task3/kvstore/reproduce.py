#!/usr/bin/env python3
import os
import shutil
from helpers.constants import RESULT_FOLDER

if os.path.exists(RESULT_FOLDER):
    shutil.rmtree(RESULT_FOLDER)
os.makedirs(f'{RESULT_FOLDER}/rocksdb')
os.makedirs(f'{RESULT_FOLDER}/memcached')

from helpers import plot
from helpers import reproduce_rocksdb
plot.plot_ycsb("result/rocksdb")
from helpers import reproduce_memcached
plot.plot_ycsb("result/memcached")
os.system("./reproduce_tpcc.sh")
plot.plot_tpcc("./result/tpcc")