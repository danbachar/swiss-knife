## Benchmarking

Prerequisites: 
- Python3
- pandas, numpy, matplotlib (installed automatically on `nix-build`)

To run benchmarks: 
1. Ensure the server you want to benchmark is running
2. run `python3 -m <folder>.benchmark` where `<folder>` is one of `basic`, `select`, `epoll`, ...
3. After the run finishes find the plot in the folder