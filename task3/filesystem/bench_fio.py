import getopt
import os
import sys
import subprocess

def fio_bench(direct_io, size, io_engine, name, block_size, io_depth, mode, filename, output):
    print("################################################################")
    print("FIO using:")
    print("Blocksize: " + block_size)
    print("File: " + filename)
    print("Direct IO: " + direct_io)
    print("################################################################")
    bash_command = 'sudo fio --randrepeat=1 --unified_rw_reporting=1 --ioengine='+io_engine+' --direct='+direct_io+' --gtod_reduce=1 --name='+name+' --bs='+block_size+' -numjobs=4 --iodepth='+io_depth+' --readwrite='+mode+' --rwmixread=50 --size='+size+' --filename=' + filename+' --output-format=json --output=' + output
    process = subprocess.Popen(bash_command, shell=True, stdout=subprocess.PIPE)
    process.wait()
