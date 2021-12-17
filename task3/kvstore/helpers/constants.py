#!/usr/bin/env python3
import random
import string

RND = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
ROCKSDB_PATH = f'/tmp/teama_rocksdb_benchmark_db_{RND}'
THREAD_COUNT_OPTION = '-threads 64'
TARGET_MULTIPLIER = 10
RESULT_FOLDER = 'result'
MIN_TARGET_POW = 10
MAX_TARGET_POW = 22