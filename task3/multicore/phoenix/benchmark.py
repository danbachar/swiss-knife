#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os 
import re
import csv
import subprocess
import multiprocessing
import matplotlib.pyplot as plt

dataDir     = "/root/dataset/"
inputSizes    = ["small","medium","large"]
textNames   = ["dickens-20M.txt", "dickens-100M.txt", "dickens-200M.txt"]  # as 500M is too heavy for the sequential version
textSets    = [ dataDir + text  for text in textNames]
keysToMatch = dataDir + "keys.txt"

params = {
    "histogram": [dataDir + bmpSize + ".bmp" for bmpSize in inputSizes],
    "kmeans": ["-d 10 -c 50 -p 10000 -s 9999","-d 10 -c 50 -p 50000 -s 9999","-d 10 -c 50 -p 100000 -s 9999"],
    "linear_regression": textSets,
    "matrix_multiply": ["100 100 matrix_file","500 500 matrix_file","1000 1000 matrix_file"],
    "pca": ["-r 300 -c 300 -s 9999","-r 500 -c 500 -s 9999","-r 1000 -c 1000 -s 9999"],
    "string_match": [keysToMatch + " " + textSet for textSet in textSets], 
    "word_count": textSets
}

programs = ["histogram", "kmeans", "pca","word_count"]
baseApps = ["hist-seq", "kmeans-seq", "pca-seq", "wordcount_serial"]

def benchmark(programs, threads, dataset, base):
    if base == True:
        data_filename = "result_seq" + "_d" + str(dataset)
        tests_dir = os.path.join(os.getcwd(), "sample_apps/")
    else:
        data_filename = "result_t" + str(threads) + "_d" + str(dataset)
        tests_dir = os.path.join(os.getcwd(), "phoenix++-1.0/tests/")

    data_filename = "/root/result/" + data_filename

    with open(data_filename, 'w') as f:
        f.write('apps,walltime\n')
        for idx in range(len(programs)):
            appdir = programs[idx]
            app = baseApps[idx] if base == True else programs[idx]
            print(f'Running app {app} with {threads} thread(s) and {inputSizes[dataset]} dataset')
            f.write(f'{app},')
            out = subprocess.check_output(f'bash -c "(time {tests_dir}{appdir}/{app} {params[appdir][dataset]}) 2>&1 >/dev/null| grep real"', shell=True, text=True)
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
    os.chdir('/root/result')
    name_list = programs
    results = []
    legends = []
    basefiles = []
    base_lists = []

    pattern = 'result_t*_d1' if mode == "threads" else 'result_t8_d*'

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

    for i in range(n):
        plt.bar(x, num_lists[i], width=width, label=(legends[i]+" Threads" if mode == "threads" else inputSizes[legends[i]]))
        for i in range(len(x)):
            x[i] = x[i] + width

    x = [i + width for i in list(range(len(num_lists[0])))]
    plt.xticks(x, labels=programs)

    plt.legend()
    plt.savefig('/root/result/result_t.png' if mode == "threads" else f'/root/result/result_d.png')

def generate_data():
    os.system('python3 ~/dataset/prepare_dataset.py')

def main():
    generate_data()
    cpu_count = multiprocessing.cpu_count()
    for threads in [1,2,4,8]:
        os.environ["MR_NUMTHREADS"] = str(threads)
        print(f'Threads Num: {threads}')
        benchmark(programs, threads, 2, False)  #fix dataset to the large one

    for dataset in range(3):
        benchmark(programs, 8, dataset, False)  #fix threads to 8
        benchmark(programs, 1, dataset, True)   #test for sequential code
    
    plot(programs,"threads")
    plot(programs,"dataset")

if __name__ == '__main__':
    main()
