from src._scheduler import SequentialScheduler
from src._common import Runner, RunnerParams
from src._benchplan import read_fastlbp_benchplan, FastlbpBenchplan
from src.execute_fastlbp_bench import main as benchmark_main
from src.parse_fastlbp_results import main as parse_main
from src._config import config

from contextlib import redirect_stderr
import sys
import os
from time import sleep

"""
Remember to check your src/config_values file!!!
"""

input_benchplan = 'benchplans/alina_3.csv'
work_benchplan = 'results_alina_3.csv'

"""
"""

# step 1
def prepare_benchplans():
    
    bp = FastlbpBenchplan()

    # 3 repetitions
    for i in range(3):
        bp.add_star_combinations_fastlbp(
            shape=[
                (20000,20000,3), # baseline
                (1000,1000,3), (2000,2000,3), (5000,5000,3), (10000,10000,3), (30000,30000,3), # shape test
                (2000,2000,1), (5000,5000,1), (10000,10000,1), # (5000,5000,2), (5000,5000,4), (5000,5000,10) # nchannels test. TODO: custom nchannels, more than 3
            ],
            maskratio=[0.0],
            patchsize=[100, 5, 10, 20, 50, 200, 500, 1000],
            ncpus=[8],
            nradii=[12, 5, 8, 15, 20]
        )

    # bp = read_fastlbp_benchplan(input_benchplan, ensure_runnable=True)
    print(f"{len(bp.all_runs)} runs")
    bp.save(work_benchplan)

# step 2
def run_benchmark():
    benchmark_main(
        bench_plan_path=work_benchplan,
        avail_cpus=config.max_ncpus,
        avail_mem_gb=config.max_mem_gb,
        parallel=True,
        check_interval = 10.0, 
        print_interval = 60.0,
        prof_poll_interval = 10.0
    )
    # OS need some time to flush logs to the files
    print("Waiting for OS to flush log files...")
    sleep(5)

# step 3
def parse_results():
    parse_main(
        benchplan_file=work_benchplan,
        results_dir='results',
        skip_unknown_runs=True
    )

if __name__ == "__main__":
    with redirect_stderr(sys.stdout):
        if os.path.exists(work_benchplan):
            print(f"'{work_benchplan}' already exists. Do you really want to OVERWRITE it and start benchmarking again? [y/n]")
            yn = input(":")
            if yn.lower() == 'y':
                print("Overwriting the benchplan")
                prepare_benchplans()
            else:
                print("Ok, I will not overwrite and will continue working on the same benchplan. I did not change the file.")
                parse_results()
        else:
            prepare_benchplans()
       
        run_benchmark()
        parse_results()
