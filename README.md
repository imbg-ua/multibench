# Benchmarking-beta

## How to run

### Step 1.
Ensure you have a suitable conda environment.  
I recommend using miniforge from https://github.com/conda-forge/miniforge.  
You can create an envvironment using `conda env create -f environment.yaml`.

### Step 2.
Change your config file at src/config_values.py

### Step 3.
Execute  
`export PYTHONPATH=/absolute/path/to/benchmarking-beta/src`  
or  
`$env:PYTHONPATH = "Y:\\absolute\path\to\benchmarking-beta\src"`

Of course you need to replace these sample paths with your own

### Step 4.
Run a selected benchplan using one of pre-made scripts, or by creating one yourself.
For example,  
```
conda activate fastlbp-benchmarking
python ./laptop_bench.py
```
and that's it. Results will be in the `laptop.result.csv`

You can stop the benchmarking using Ctrl+C

If benchmarking is interrupted, you can continue from where you've stopped simply by running it again and answering "NO" when it asks you about overwriting the results.

**Important note about stopped benchmarking: you should stop all python processes yourself using your system's task manager. Otherwise, the next benchmarking would be inaccurate and results will be unusable.**  
Search for strings with 'multiprocessing' or 'fastlbp'.  
Sorry, I have not implemented an automatic cleanup yet.

## A custom benchmark

### Step 1.
Create a bench plan. This is a list of parameters for each job.
- Edit and run src/prepare_fastlbp_bench.py
- Or create bench_plan csv manually and then run `_benchplan.read_fastlbp_benchplan('bench_plan.csv', ensure_runnable=True)`

### Step 2.
Run a fastlbp benchplan (src/execute_fastlbp_bench.py)  
or create a custom executor based on it.

### Step 3.
Parse results with `src/parse_fastlbp_results.py <benchplan_file> <results_dir>`.  
This script will go through your `results_dir` with `mem_*.log` files, find all results for a selected benchplan,
and create a copy of your benchplan called './results_<yourbenchplan>.csv' with columns result_mem, result_time and result_ok filled.

Note that it only works 1) for fastlbp, 2) for log files with names starting with 'mem_' (don't ask why),
and 3) when both .log and .err files are present.

Have fun!
