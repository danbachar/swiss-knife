#!/usr/bin/env python3
import os
import shutil
from helpers.constants import RESULT_FOLDER

if os.path.exists(RESULT_FOLDER):
    shutil.rmtree(RESULT_FOLDER)
os.makedirs(f'{RESULT_FOLDER}/rocksdb')
os.makedirs(f'{RESULT_FOLDER}/memcached')

from helpers import reproduce_rocksdb, reproduce_memcached, plot
