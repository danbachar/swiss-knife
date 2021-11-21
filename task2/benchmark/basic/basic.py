
import os
import matplotlib.pyplot as plt
import pandas as pd


BASIC_DATA_FILENAME = 'basic_bench_output.csv'
BASIC_PLOT_FILENAME = 'basic_plot.png'
BASIC_PORT = 8081

CONNECTIONS = 'Connections'
REQS_PER_SEC = 'Requests/Second'


def benchmark(data_filename, plot_filename, port):
    with open(data_filename, 'w') as f:
        f.write(f'{CONNECTIONS},{REQS_PER_SEC}\n')
        f.flush()
        for i in range(10, 101, 10):
            print(f'Running wrk with {i} connections')
            f.write(f'{i},')
            f.flush()
            out = os.popen(
                f'wrk -t 10 -c {i} http://localhost:{port} | grep Requests/sec')
            line = out.read()
            recsPerSec = line.split(' ')[-1]
            print('requests per second', recsPerSec)
            f.write(recsPerSec)
            f.flush()

    df = pd.read_csv(data_filename)
    print(df)
    df.plot(x=CONNECTIONS, y=REQS_PER_SEC, ylim=[0, 110000])
    plt.savefig(plot_filename)


benchmark(BASIC_DATA_FILENAME, BASIC_PLOT_FILENAME, BASIC_PORT)
