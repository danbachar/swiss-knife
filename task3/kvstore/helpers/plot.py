#!/usr/bin/env python3

import pandas as pd
import os
import matplotlib.pyplot as plt
import sys


def read_result(filename, df: pd.DataFrame):
    with open(filename, "r") as f:
        lines = list(filter(lambda line: "Throughput(ops/sec)" in line or "AverageLatency(us)" in line, f.readlines()))
        lines = list(filter(lambda line: "CLEANUP" not in line, lines))
        values = {
            line.split(" ")[0][:-1] + ' ' + line.split(" ")[1][:-1]: [float(line.split(" ")[-1][:-1])] 
            for line in lines
        }
        values_df = pd.DataFrame(values)
        if not df.empty:
            df = df.append(values_df)
            return df
        else:
            return values_df
        

def plot_ycsb(dir):
    files = os.listdir(dir)
    a_files = list(filter(lambda x: "_a_" in x, files))
    b_files = list(filter(lambda x: "_b_" in x, files))
    c_files = list(filter(lambda x: "_c_" in x, files))
    d_files = list(filter(lambda x: "_d_" in x, files))
    e_files = list(filter(lambda x: "_e_" in x, files))
    f_files = list(filter(lambda x: "_f_" in x, files))
    g_files = list(filter(lambda x: "_g_" in x, files))

    for workload, file_list in [('a', a_files), ('b', b_files), ('c', c_files), ('d', d_files), ('e', e_files), ('f', f_files), ('g', g_files)]:
        df = pd.DataFrame()
        for filename in file_list:
            df = read_result(dir + '/' + filename, df)
        df.sort_values(by='[OVERALL] Throughput(ops/sec)' ,inplace=True)
        df.plot(x=0, y=df.columns[1:], kind="line")
        plt.savefig(f'{dir}_{workload}_plot.png')
        
def read_tpcc_result(filename, df: pd.DataFrame) -> pd.DataFrame:
    with open(filename, "r") as f:
        lines = f.readlines()
        threads = list(filter(lambda line: "Number of threads:" in line, lines))
        tps = list(filter(lambda line: "transactions:" in line, lines))
        values = {
            "Threads": [0] if len(threads) == 0 else [int(list(filter(lambda x: x != "", threads[0].split(" ")))[-1][:-1])],
            "Transactions/Sec": [0.0] if len(tps) == 0 else [float(tps[0].split("(")[1].split(" ")[0])],
        }
        print("values", values)
        values_df = pd.DataFrame(values)
        if not df.empty:
            df = df.append(values_df)
            return df
        else:
            return values_df    
        
def plot_tpcc(dir):
    files = os.listdir(dir)
    df = pd.DataFrame()
    for filename in files:
        df = read_tpcc_result(os.path.join(dir, filename), df)
    print(df)
    df.sort_values(by='Threads' ,inplace=True)
    df.plot(x=0, y=df.columns[1:], kind="line", logx=True)
    plt.savefig(f'result/tpcc_plot.png')
        

if len(sys.argv) >= 2:
    plot_ycsb(sys.argv[1])
    