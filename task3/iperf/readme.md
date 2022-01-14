# Network benchmark

To reproduce benchmarks steps, be sure to be in the **nix environment**: use
> $ nix-shell

in repository's root.

# Basic task
## Intro
for launching the process, simply run 
>$ python server.py [-t duration_of_each_test_in_seconds (default 10s) -c number_of_parallel_connections (default 1) -f data_filename -d plot_filename -p port (default 5201)]

and everything will start working.

## Benchmarks

Everything is automated in the basic task's benchmark, at the end you can find some utility .csv files under the `plots` folder that you can analyze for further researches, but most importantly you can find the plots created. The files have the following naming scheme: `plot_filename[_parallel|_ws|_ps|][_jitter|_loss|].png` which means either the parallel 1-number_of_parallel_connections test, TCP window size test, payload size test, measuring jitter, loss and speed. Having a null entry in the naming scheme above means either default for the first brackets (means the results of the test executed with the user inputted values, with default values standing in for options that the user didn't input) or speed for the second pair of brackets


# Exploration task
## Intro
for launching the process, simply run 
>$ python explore-task.py [all options from basic task, and: -l payload_length -M max_mss -o output_to_log_filename -w TCP_window_size -R(enable reverse mode) Z(use zerocopy) J(output json instead of message) x(perform only parallelism test and export the plot, following the normal naming scheme) ]

## Benchmarks


The wide possibilities of the exploration task has made this automation more complicated, thus we created only one plot, that considered the effect an increasing number of parallel connections has had on the measured performance.
