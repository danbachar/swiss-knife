# Filesystem benchmark

To reproduce benchmarks steps, be sure to be in the **nix environment**: use
> $ nix-shell

in repository's root.


# Getting started
for launch the process, simply run 
>$ python reproduce.py

and everything will start working.

# FIO Benchmark

Everything is automated in FIO's benchmark, at the end you can find some utils .json file that you can analyze for further researches, but most importantly you can find a **blocksize.png** that will be the final plot.

## Phoronix Benchmark

The nature of Phoronix benchmark has made this automation way more complicated.
While *copying to the file systems and syslinking to user's home* steps are automated for both measurements, user will end up using bash input to select options for the benchmark.
In order, the user should input:

 - 4
 - y
 - a name that will be meaningful for the FS, keeping in mind BTRFS measurement comes before EXT4 ones
 - then always press y to confirm and upload data to the server
at the end of the bench you can find a link to follow and see the plot.
