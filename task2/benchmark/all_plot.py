import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

CONNECTIONS = 'Connections'
REQS_PER_SEC = 'Requests/Second'

def plot(plot_filename):
    data_files = ["server.csv", "server_epoll.csv", 
                    "server_epoll_multiprocess.csv", "server_select.csv", 
                    "server_thread.csv", "server_uring.csv"]
    df0 = pd.read_csv(data_files[0])
    df1 = pd.read_csv(data_files[1])
    df2 = pd.read_csv(data_files[2])
    df3 = pd.read_csv(data_files[3])
    df4 = pd.read_csv(data_files[4])
    df5 = pd.read_csv(data_files[5])

    a = df0.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='basic', color="Red")
    b = df1.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='epoll', color="Green", ax = a)
    c = df2.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='epoll multiprocess', color="Yellow", ax = b)
    d = df3.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='select', color="Blue", ax = c)
    e = df4.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='basic multithreaded', color="Orange", ax = d)
    f = df5.plot(x=CONNECTIONS, y=REQS_PER_SEC, label='io_uring', color="DarkBlue", ax = e)
    plt.savefig(plot_filename)


def main(argv):
    os.chdir('./plots')
    plot('all_plot.png')


if __name__ == '__main__':
    main(sys.argv[1:])
