import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json
import math

def extract(filename,access):
    f = open(filename)
    data = json.load(f)
    return eval("data"+access)


def execute(data, plot_filename):
    labels = ['128k','256k','512k']
    print(labels)
    ext4_direct = list(map(lambda x: x.get('value'),sorted(list(filter(lambda x: (x.get("filesystem") == "/mnt/teama-ext4/" and x.get("direct_io") == "1"), data)),key=lambda x: x.get('index'))))
    ext4_cache = list(map(lambda x: x.get('value'),sorted(list(filter(lambda x: (x.get("filesystem") == "/mnt/teama-ext4/" and x.get("direct_io") == "0"), data)),key=lambda x: x.get('index'))))
    btrfs_direct = list(map(lambda x: x.get('value'),sorted(list(filter(lambda x: (x.get("filesystem") == "/mnt/teama-btrfs/" and x.get("direct_io") == "1"), data)),key=lambda x: x.get('index'))))
    btrfs_cache = list(map(lambda x: x.get('value'),sorted(list(filter(lambda x: (x.get("filesystem") == "/mnt/teama-btrfs/" and x.get("direct_io") == "0"), data)),key=lambda x: x.get('index'))))

    print("ext4_direct: "+str(ext4_direct))
    print("ext4_cache: "+str(ext4_cache))
    print("btrfs_direct: "+str(btrfs_direct))
    print("btrfs_cache: "+str(btrfs_cache))

    x = np.arange(len(labels))  # the label locations
    width = 0.20 # the width of the bars

    fig, ax = plt.subplots()

    rects1 = ax.bar(x - (width/2)*3, btrfs_direct, width, label='BTRFS + Direct IO')
    rects2 = ax.bar(x - width/2, ext4_direct, width, label='EXT4 + Direct IO')
    rects3 = ax.bar(x + width/2, btrfs_cache, width, label='BTRFS + Buffered IO')
    rects4 = ax.bar(x + (width/2)*3, ext4_cache, width, label='EXT4 + Buffered IO')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Bits')
    ax.set_title('Random Read Bandwidth by blocksize')
    print("x:" + str(x))
    ax.set_xticks(x)
    ax.set_ylim(4500000,8000000)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.savefig(plot_filename)
