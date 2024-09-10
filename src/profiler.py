# from memory_profiler import memory_usage
import psutil
import subprocess
import os
import time
import datetime

# https://github.com/imbg-ua/fastLBP-sandbox/blob/main/lbp-playground/true-memory-profiling.ipynb

from _config import config
from _common import Runner, RunnerParams

PROFILER_VER = "0.0.1"

class Profiler:
    outfile: str
    poll_interval_s: float
    full_mem_info: bool

    def __init__(self, outfile='./memory', poll_interval_s: float = 0.1, full_mem_info: bool = False):
        self.poll_interval_s = poll_interval_s
        self.outfile = outfile
        self.full_mem_info = full_mem_info

    def profile_memory_summing(self, *popen_args, **popen_kwargs):
        import pandas as pd
        import numpy as np
        with subprocess.Popen(*popen_args, **popen_kwargs) as p:
            psp = psutil.Process(p.pid)
            
            meminfo = psp.memory_info()
            memlog = []

            p.poll()
            while p.returncode is None:
                # print("a")
                # calculate real memory usage for all children processes.
                # sum it up and save peak usage.
                proc_mem = np.array(psp.memory_info())
                subproc_mem = np.array([ list(ps_child.memory_info()) for ps_child in psp.children(True) ], dtype=np.int64)
                total_mem = proc_mem + subproc_mem.sum(axis=0)
                memlog.append(total_mem)
                time.sleep(self.poll_interval_s)
                p.poll() # update p.returncode value
            print("done")

            memlog = pd.DataFrame(columns=list(meminfo._fields))
            memlog.to_csv(self.outfile)

    def profile_memory_writing(self, *popen_args, **popen_kwargs):
        with \
            open(self.outfile, 'w', encoding='utf-8') as f, \
            subprocess.Popen(*popen_args, **popen_kwargs) as p:

            ps_parent = psutil.Process(p.pid)
            
            if self.full_mem_info:
                meminfo = ps_parent.memory_full_info()
            else:
                meminfo = ps_parent.memory_info()
            header = "time,pid,is_parent," + ','.join(meminfo._fields) + '\n'
            f.write(header)

            t0 = time.perf_counter()
            p.poll()
            while p.returncode is None:
                now = time.perf_counter() - t0
                if self.full_mem_info:
                    parent_mem = ps_parent.memory_full_info()
                else:
                    parent_mem = ps_parent.memory_info() 
                parent_str = f"{now:.3f},{ps_parent.pid},1," + ','.join(map(str,parent_mem)) + '\n' 
                f.write(parent_str)

                for ps_child in ps_parent.children(True):
                    if self.full_mem_info:
                        child_mem = ps_child.memory_full_info()
                    else:
                        child_mem = ps_child.memory_info() 
                    child_str = f"{now:.3f},{ps_child.pid},0," + ','.join(map(str,child_mem)) + '\n' 
                    f.write(child_str)

                time.sleep(self.poll_interval_s)
                p.poll() # update p.returncode value
            print("done")

def plot():
    pass

def test():
    from fastlbp_runner import FastlbpRunner, FastlbpRunnerParams

    params = FastlbpRunnerParams('test', 'input/img_L_5000x5000.tiff', None, 50, 4, 5)

    with open('fastlbp.out', 'w') as outf, \
         open('fastlbp.err', 'w') as errf:
        prof = Profiler(poll_interval_s=0.5)
        argv = FastlbpRunner.get_argv(params)
        print(argv)
        prof.profile_memory_writing(argv, stdout=outf, stderr=errf)
    
    print("Exiting main.")

def main(*target_argv: str, outfile:str = None, poll_interval_s: float = 0.1, full_memory_info: bool = True):
    print(f"welcome to profiler ver {PROFILER_VER}")
    print(f"profiling {target_argv[0]}")
    print(f"see executable output at {outfile}.out(.err)")
    print(f"see memory profiling at {outfile}.log")
    
    if outfile is None:
        outfile = "profile_" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    with open(f'{outfile}.out', 'w') as outf, \
         open(f'{outfile}.err', 'w') as errf:
        prof = Profiler(
            poll_interval_s=poll_interval_s, 
            outfile=f'{outfile}.log', 
            full_mem_info=full_memory_info)
        print("profiling argv: ", target_argv)
        target_argv_str = list(map(str, target_argv))
        prof.profile_memory_writing(target_argv_str, stdout=outf, stderr=errf)

"""
"""

from typing import Type

def make_profiling_runner(base_runner_class: Type[Runner], profiler_instance: Profiler, results_dir: str = '.'):
    """
    Create a runner that starts a profiler for each job.
    Profiling params are loaded from `profiler_instance`
    Profiler will write results to a `results_dir`, which is a job cwd by default.
    """
    class ProfilingRunner(base_runner_class):
        @staticmethod
        def get_argv(params: RunnerParams) -> list[str]:
            # profile_name:str = None, poll_interval_s: float = 0.1, full_memory_info
            profile_name, poll_interval_s, full_memory_info = \
                profiler_instance.outfile, profiler_instance.poll_interval_s, profiler_instance.full_mem_info
            return ['python', os.path.join(config.src_root, 'profiler.py'), 
                    '--outfile="'+os.path.join(results_dir, 'mem_'+params.run_label)+'"', 
                    f'--poll_interval_s={poll_interval_s}', 
                    f'--full_memory_info={full_memory_info}'] + base_runner_class.get_argv(params)

        @staticmethod
        def main(*args, **kwargs):
            main(*args, **kwargs)
    
    return ProfilingRunner

"""
"""


if __name__ == "__main__":
    import fire
    fire.Fire(main)
