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
        

def plot(dir):
    files = os.listdir(dir)
    a_files = list(filter(lambda x: "_a_" in x, files))
    b_files = list(filter(lambda x: "_b_" in x, files))
    c_files = list(filter(lambda x: "_c_" in x, files))
    d_files = list(filter(lambda x: "_d_" in x, files))
    e_files = list(filter(lambda x: "_e_" in x, files))
    f_files = list(filter(lambda x: "_f_" in x, files))
    g_files = list(filter(lambda x: "_g_" in x, files))

    for workload, file_list in [('g', g_files)]:
        df = pd.DataFrame()
        for filename in file_list:
            df = read_result(dir + '/' + filename, df)
        print(df)
        df.sort_values(by='[OVERALL] Throughput(ops/sec)' ,inplace=True)
        print(df)
        df.plot(x=0, y=df.columns[1:], kind="line")
        plt.savefig(f'{dir}_{workload}_plot.png')
        
if len(sys.argv) < 2:
    print("Directory with YCSB results required")
    exit(1)
    
plot(sys.argv[1])