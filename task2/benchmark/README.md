## Benchmarking

Prerequisites: 
- Python3
- pandas, numpy, matplotlib (installed automatically on `nix-build`)

To run benchmarks: 
1. Ensure the server you want to benchmark is running
2. `cd` to the folder with the benchmark (i.e. `cd epoll` before benchmarking `server_poll`)
3. run `python3 benchmark.py`
4. After the run finishes find the plot in the folder