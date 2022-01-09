#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os 
import re
import csv
import subprocess
import multiprocessing
import matplotlib.pyplot as plt

programs = ["blackscholes","bodytrack","ferret","fluidanimate","freqmine","swaptions","vips"] # remove raytrace, as its threaded version blocks, also remove facesim and x264, as they meet segment fault 
inputs   = ["simsmall","simmedium","simlarge"]
configs  = ["gcc-serial","gcc"]
resultDir = "/home/result/"

def benchmark(programs, threads, dataset, base):
    data_filename = resultDir + ("result_seq" + "_d" + str(dataset) if base == True else "result_t" + str(threads) + "_d" + str(dataset))
    config = configs[0] if base == True else configs[1] 

    with open(data_filename, 'w') as f:
        f.write('apps,walltime\n')
        for app in programs:
            print(f'Running app {app} with {threads} thread(s) and {inputs[dataset]} dataset')
            f.write(f'{app},')
            out = subprocess.check_output(f'parsecmgmt -a run -p {app} -c {config} -i {inputs[dataset]} -n {threads} | grep real', shell=True, text=True)
            seconds = re.findall(".*m(.*)s.*", out)[0]
            minutes = re.findall("real(.*)m.*", out)[0]
            wallTime = str(int(minutes)*60 + float(seconds))
            print('wall time:', wallTime)
            f.write(wallTime+'\n')
            f.flush()

import matplotlib.pyplot as plt
import pandas as pd
import fnmatch
def plot(programs, mode):
    os.chdir(resultDir)
    name_list = programs
    results = []
    legends = []
    basefiles = []
    base_lists = []

    pattern = 'result_t*_d2' if mode == "threads" else 'result_t8_d*'

    for f_name in os.listdir('./'):
        if fnmatch.fnmatch(f_name, pattern):
            results.append(f_name)
        elif fnmatch.fnmatch(f_name, 'result_seq_d*'):
            basefiles.append(f_name)
    results.sort()
    basefiles.sort()

    for basefile in basefiles:
        df = pd.read_csv(basefile, delimiter=',')
        base_list = list(df.to_dict()["walltime"].values())
        base_lists.append(base_list)

    legends = [(f_name[8:f_name.find('d')] 
                if mode == "threads" 
                else int(f_name[f_name.find('d')+1:])) for f_name in results]
    
    num_lists = []
    datasetSize = 0
    for result in results:
        df = pd.read_csv(result, delimiter=',')
        num_list = list(df.to_dict()["walltime"].values())
        if mode == "threads":
            num_list = [base_lists[2][i] / num_list[i] for i in range(len(num_list))]
        if mode == "dataset":
            num_list = [base_lists[datasetSize][i] / num_list[i] for i in range(len(num_list))]
        num_lists.append(num_list)
        datasetSize = datasetSize + 1 

    x =list(range(len(num_lists[0])))
    total_width = 0.8
    n = len(results)
    width = total_width / n

    plt.figure(figsize=(12, 6.5))
    plt.title("corenum comparison" if mode == "threads" else "dataset comparison")

    for i in range(n):
        plt.bar(x, num_lists[i], width=width, label=(legends[i]+" Threads" if mode == "threads" else inputs[legends[i]]))
        for j in range(len(x)):
            plt.text(x[j], 0, str(round(num_lists[i][j],1)), ha='center', va='bottom', fontsize=5, color='black')
        for i in range(len(x)):
            x[i] = x[i] + width

    x = [i + width for i in list(range(len(num_lists[0])))]
    plt.xticks(x, labels=programs)
    plt.xlabel("Programs")
    plt.ylabel("Speed Up")


    plt.legend()
    plt.savefig('result_t.png' if mode == "threads" else f'result_d.png')

def main():
    cpu_count = multiprocessing.cpu_count()
    for threads in [1,2,4,8]:
        print(f'Threads Num: {threads}')
        benchmark(programs, threads, 2, False)  #fix dataset to the large one

    for dataset in range(3):
        benchmark(programs, 8, dataset, False)  #fix threads to 8
        benchmark(programs, 1, dataset, True)   #test for sequential code
    
    plot(programs,"threads")
    plot(programs,"dataset")

if __name__ == '__main__':
    main()
