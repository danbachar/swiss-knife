import pandas as pd
import matplotlib.pyplot as plt
import os

BASIC_DATA_FILENAME = 'basic_bench_output.csv'
CONNECTIONS = 'Connections'
REQS_PER_SEC = 'Requests/Second'

with open(BASIC_DATA_FILENAME, 'w') as f:
    f.write(f'{CONNECTIONS},{REQS_PER_SEC}\n')
    f.flush()
    for i in range(10, 101, 10):
        print(f'Running wrk with {i} connections')
        f.write(f'{i},')
        f.flush()
        out = os.popen(
            f'wrk -t 10 -c {i} http://localhost:8081 | grep Requests/sec')
        line = out.read()
        recsPerSec = line.split(' ')[-1]
        print('requests per second', recsPerSec)
        f.write(recsPerSec)
        f.flush()
df = pd.read_csv(BASIC_DATA_FILENAME)
print(df)
df.plot(x=CONNECTIONS, y=REQS_PER_SEC, xlim=[0, 110])
plt.savefig('basic_plot.png')
