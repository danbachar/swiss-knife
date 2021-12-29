#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os 
import csv
import multiprocessing
import matplotlib.pyplot as plt

dataDir     = "/root/dataset/"
inputSizes    = ["small","medium","large"]
textNames   = ["dickens-100M.txt", "dickens-500M.txt", "dickens-1G.txt"]
textSets    = [ dataDir + text  for text in textNames]
keysToMatch = dataDir + "keys.txt"

params = {
    "histogram": [dataDir + bmpSize + ".bmp" for bmpSize in inputSizes],                                      # inputsize scale: 25, 125
    "kmeans": ["-d 10 -c 50 -p 10000 -s 9999","-d 10 -c 50 -p 50000 -s 9999","-d 10 -c 50 -p 100000 -s 9999"],# inputsize scale: 25, 100
    "linear_regression": textSets,                                                                            # inputsize scale: 5, 10
    "matrix_multiply": ["100 100 matrix_file","500 500 matrix_file","1000 1000 matrix_file"],                 # inputsize scale: 25, 100
    "pca": ["-r 100 -c 100 -s 9999","-r 500 -c 500 -s 9999","-r 1000 -c 1000 -s 9999"],                       # inputsize scale: 25, 100
    "string_match": [keysToMatch + " " + textSet for textSet in textSets], 
    "word_count": textSets                                                                                    # inputsize scale: 5,10
}

programs = ["histogram", "kmeans", "linear_regression","matrix_multiply","pca","string_match","word_count"]
scale = [[1,25,125],[1,25,100],[1,5,10],[1,25,100],[1,25,100],[1,5,10],[1,5,10]]
usedCPU = 1

def benchmark(programs, threads, dataset):
    data_filename = "result_t" + str(threads) + "_d" + str(dataset)
    tests_dir = os.path.join(os.getcwd(), "tests/")

    with open(data_filename, 'w') as f:
        f.write('apps,walltime\n')
        for app in programs:
            print(f'Running app {app} with {threads} thread(s) and {inputSizes[dataset]} dataset')
            f.write(f'{app},')
            out = os.popen(
                f'{tests_dir}{app}/{app} {params[app][dataset]} 2>&1 | grep "^library :"')
            print(f'{tests_dir}{app}/{app} {params[app][dataset]} 2>&1 | grep "^library :"')
            line = out.read()
            wallTime = line.split(' ')[-1]
            print('wall time:', wallTime)
            f.write(wallTime)
            f.flush()

import matplotlib.pyplot as plt
import pandas as pd
import fnmatch
def plot(programs, mode):
    name_list = programs
    results = []
    legends = []

    global usedCPU
    pattern = 'result_t*_d1' if mode == "threads" else f'result_t{usedCPU}_d*'

    for f_name in os.listdir('./'):
        if fnmatch.fnmatch(f_name, pattern):
            results.append(f_name)
    results.sort()

    legends = [(f_name[8:f_name.find('d')] 
                if mode == "threads" 
                else int(f_name[f_name.find('d')+1:])) for f_name in results]
    
    num_lists = []
    datasetSize = 0
    for result in results:
        df = pd.read_csv(result, delimiter=',')
        num_list = list(df.to_dict()["walltime"].values())
        if mode == "dataset":
            num_list = [num_list[i] / scale[i][datasetSize] for i in range(len(num_list))]
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
    global usedCPU
    cpu_count = multiprocessing.cpu_count()
    for threads in range(1,cpu_count+1, cpu_count/4 if cpu_count>4 else 1):
        os.environ["MR_NUMTHREADS"] = str(threads)
        usedCPU = threads
        print(f'Threads Num: {threads}')
        benchmark(programs,threads,1)  #fix dataset to the medium one

    for dataset in range(3):
        benchmark(programs,usedCPU,dataset)  #fix threads to maximum

    plot(programs,"threads")
    plot(programs,"dataset")

if __name__ == '__main__':
    main()
