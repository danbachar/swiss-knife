import getopt
import os
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import netifaces as ni

CONNECTIONS = 'Connections'
REQS_PER_SEC = 'Requests/Second'
DATA_FILENAME = 'benchmark_output.csv'
PLOT_FILENAME = 'benchmark_plot.png'
PORT = 8081

# retrieve the ip address of the swissknife0 interface
ip = list(
    filter(lambda ip: "swissknife1" in ip,
           (map(lambda ip: ip["addr"],
                ni.ifaddresses('swissknife1')[ni.AF_INET6])
            )
           )
).pop()
URL = f"http://[{ip}]"


def benchmark(data_filename, plot_filename, port):
    with open(data_filename, 'w') as f:
        f.write(f'{CONNECTIONS},{REQS_PER_SEC}\n')
        f.flush()
        for i in range(10, 101, 10):
            print(f'Running wrk with {i} connections')
            f.write(f'{i},')
            f.flush()
            out = os.popen(
                f'wrk -t 10 -c {i} {URL}:{port} | grep Requests/sec')
            line = out.read()
            recsPerSec = line.split(' ')[-1]
            print('requests per second', recsPerSec)
            f.write(recsPerSec)
            f.flush()

    df = pd.read_csv(data_filename)
    print(df)
    df.plot(x=CONNECTIONS, y=REQS_PER_SEC)
    plt.savefig('./plots/' + plot_filename)

def flamegraph(flamegraph_filename, port):
    out = os.popen(
        f'wrk -t 10 -c 1000 -d 10 {URL}:{port} &')
    out = os.popen(
        f'sudo profile -F 99 -adf 10 > ./plots/{flamegraph_filename}_folded &')
    time.sleep(15)
    out = os.popen(
        f'perl ./FlameGraph/flamegraph.pl --colors=java ./plots/{flamegraph_filename}_folded > ./plots/{flamegraph_filename}.svg')
       

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "p:f:d:",
                                   ["port=" "plot_filename=" "data_filename="])
    except getopt.GetoptError:
        print("Syntax Error.")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-p", "--port"):
            global port
            port = arg
        elif opt in ("-f", "--filename_plot"):
            global plot_filename
            plot_filename = arg + ".png"
            flamegraph_filename = arg
        elif opt in ("-d", "--filename_data"):
            global data_filename
            data_filename = arg + ".csv"
    benchmark(data_filename, plot_filename, port)
    flamegraph(flamegraph_filename, port)

if __name__ == '__main__':
    main(sys.argv[1:])
