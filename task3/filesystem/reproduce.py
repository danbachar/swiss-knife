import sys

import bench_fio as bench
import plot_fio as plot
import phoronix_bench as fsmark

FS = ["/mnt/teama-btrfs/", "/mnt/teama-ext4/"]
BS = ["128k","256k","512k"]
DIR_IO = ["1","0"]

def reproduce():
    data = []
    #BASIC TASK : plotting different blocksizes with both FS and DirectIO / CachedIO
    for filesystem in FS:
        for io in DIR_IO:
            index=0
            for blocksize in BS:
                bench.fio_bench(io, "30G", "io_uring", "_"+blocksize+"_"+filesystem+"_"+io, blocksize, "8", "randread", filesystem+"testfile.txt", (blocksize+"_"+filesystem+"_"+io+"_.json").replace("/","_"))
                job_desc = {
                    "index": index,
                    "export_name": (blocksize+"_"+filesystem+"_"+io+"_.json").replace("/","_"),
                    "filesystem": filesystem,
                    "blocksize": blocksize,
                    "direct_io": io,
                    "size": "30G",
                    "mode": "randrw",
                    "label": blocksize,
                    "value": plot.extract((blocksize+"_"+filesystem+"_"+io+"_.json").replace("/","_"),"['jobs'][0]['mixed']['bw']")
                }
                data.append(job_desc)
                index+=1
    plot.execute(data, "blocksize.png")

    #EXPLORATION TASK: PHORONIX SECTION BELOW
    fsmark.execute_env(FS)

def main(argv):
    reproduce()

if __name__ == '__main__':
    main(sys.argv[1:])
