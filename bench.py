from src._scheduler import SequentialScheduler
from src._common import Runner, RunnerParams
from src._benchplan import read_fastlbp_benchplan
from src.execute_fastlbp_bench import main as benchmark_main
from src.parse_fastlbp_results import main as parse_main
from src._config import config

from contextlib import redirect_stderr
import sys
from time import sleep
import os

"""
Remember to check your src/config_values file!!!
"""

# step 1
def prepare_benchplans(input_benchplan, work_benchplan):
    bp = read_fastlbp_benchplan(input_benchplan, ensure_runnable=True)
    print(f"{len(bp.all_runs)} runs")
    bp.save(work_benchplan)

# step 2
def run_benchmark(input_benchplan, work_benchplan):
    benchmark_main(
        bench_plan_path=work_benchplan,
        avail_cpus=config.max_ncpus,
        avail_mem_gb=config.max_mem_gb,
        parallel=True
    )
    print("Waiting for OS to flush log files...")
    sleep(5)

# step 3
def parse_results(input_benchplan, work_benchplan):
    parse_main(
        benchplan_file=work_benchplan,
        results_dir='results',
        skip_unknown_runs=True
    )

def execute_bench(input_benchplan, work_benchplan):
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
