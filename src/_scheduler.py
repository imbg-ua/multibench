import os
import subprocess
from dataclasses import dataclass
from typing import Any, Type
import io
from time import perf_counter, sleep
# import pyinstrument

import logging
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-5s %(name)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


from _config import config
from _common import Runner, RunnerParams

"""
"""

@dataclass
class Job:
    ncpus: int
    mem_gb: int
    params: RunnerParams
    start_time: float | None
    finished_time: float | None
    process: subprocess.Popen | None
    stdout: io.IOBase | None
    stderr: io.IOBase | None

    def __init__(self, ncpus: int, mem_gb: int, params: RunnerParams):
        self.ncpus = ncpus
        self.mem_gb = mem_gb
        self.params = params
        self.start_time = None
        self.finished_time = None
        self.process = None
        self.stdout = None
        self.stderr = None
    
    def copy(self):
        newjob = Job(self.ncpus, self.mem_gb, self.params) 
        return newjob

class ParallelScheduler:
    logger = logging.getLogger('scheduler')
    logger.setLevel(logging.INFO)

    runner_class: Type[Runner]
    free_cpus: int
    free_mem_gb: int
    poll_interval_s: float
    print_interval_s: float

    queued : list[Job]
    in_progress : list[Job]
    finished : list[Job]
    last_poll_time: float
    last_print_time: float
    start_time: float

    def __init__(self, 
                 runner_class: Type[Runner], 
                 available_cpus: int, 
                 available_mem_gb: int, 
                 poll_interval_s: float = 10, 
                 print_interval_s: float = 60
                 ):
        self.runner_class = runner_class
        self.free_cpus = available_cpus
        self.free_mem_gb = available_mem_gb
        self.poll_interval_s = poll_interval_s
        self.print_interval_s = print_interval_s
        
        self.queued = []
        self.in_progress = []
        self.finished = []
        self.last_poll_time = 0
        self.last_print_time = 0
        self.start_time = 0
        self.logger.info('init')

    def _start_job(self, job: Job) -> Job:
        assert self.free_cpus >= job.ncpus
        assert self.free_mem_gb >= job.mem_gb
        self.free_cpus -= job.ncpus
        self.free_mem_gb -= job.mem_gb
        cwd = self.runner_class.get_cwd(job.params)
        new_job = job.copy()
        new_job.stdout = open(os.path.join(cwd, job.params.run_label + '.out'), 'w')
        new_job.stderr = open(os.path.join(cwd, job.params.run_label + '.err'), 'w')
        new_job.process = subprocess.Popen(
            args=self.runner_class.get_argv(job.params), 
            cwd=cwd,
            stdout=new_job.stdout, 
            stderr=new_job.stderr
        )
        new_job.start_time = perf_counter()
        self.logger.info(f"Started job '{new_job.params.run_label}' with pid {new_job.process.pid}")
        return new_job
    
    def _finalize_job(self, job: Job) -> None:
        assert job.process.poll() is not None
        self.free_cpus += job.ncpus
        self.free_mem_gb += job.mem_gb
        job.finished_time = perf_counter()
        job.stdout.close()
        job.stderr.close()
        self.logger.info(f'finalized job {job.params.run_label}')
    
    def _process_jobs_in_queue(self) -> None:
        self.logger.debug(f'_process_jobs_in_queue (q{len(self.queued)}, pr{len(self.in_progress)})')
        i = 0
        while i < len(self.queued):
            # TODO: THIS LOOP IS MALFUNCTIONING. need to adjust indexing after pop. still works tho
            job = self.queued[i]
            if self.free_cpus >= job.ncpus and self.free_mem_gb >= job.mem_gb:
                new_job = self._start_job(job)
                self.in_progress.append(new_job)
                self.queued.pop(i)
            i += 1

    def _process_jobs_in_progress(self) -> None:
        self.logger.debug(f'_process_jobs_in_progress  (q{len(self.queued)}, pr{len(self.in_progress)})')
        i = 0
        while i < len(self.in_progress):
            # TODO: THIS LOOP IS MALFUNCTIONING. need to adjust indexing after pop. still works tho
            job = self.in_progress[i]
            if job.process.poll() is not None:
                self._finalize_job(job)
                self.finished.append(job)
                self.in_progress.pop(i)
            i += 1

    def _print_info(self):
        now = perf_counter()
        self.logger.info(f"{now-self.start_time:.3f}s : {len(self.queued)} queued, {len(self.in_progress)} in progress, {len(self.finished)} finished. Avail.CPU: {self.free_cpus}, avail.Mem: {self.free_mem_gb} GB")

    def _update(self) -> None:
        self.logger.debug('start _update')
        self._process_jobs_in_progress()
        self._process_jobs_in_queue()

        # prevent infinite loop
        if len(self.in_progress) == 0 and len(self.queued) > 0:
            self.logger.warn('Cannot run anything -- not enough resources -- clearing the queue and aborting.')
            self.queued.clear()

        now = perf_counter()
        if now - self.last_print_time > self.print_interval_s:
            self._print_info()
            self.last_print_time = now
        self.last_poll_time = now
        self.logger.debug('finish _update')

    def add_job(self, ncpus: int, mem_gb: int, params: RunnerParams):
        self.logger.info("A " + params.run_label)
        self.queued.append(Job(ncpus, mem_gb, params))

    def run(self):
        self.start_time = perf_counter()
        self.logger.info(f"Starting Scheduler with {self.runner_class.__name__} runner.")
        self.logger.info(f"{len(self.queued)} jobs queued. Avail.CPU: {self.free_cpus}, avail.Mem: {self.free_mem_gb} GB.")
        
        while len(self.queued) > 0:
            self._update()
            sleep(self.poll_interval_s)

        self.logger.info("Scheduler Queue empty. Exiting.")

"""
"""

class SequentialScheduler(ParallelScheduler):
    logger = logging.getLogger('sequential_scheduler')
    logger.setLevel(logging.INFO)

    def add_job(self, ncpus: int, mem_gb: int, params: RunnerParams):
        self.logger.info("A " + params.run_label)
        self.queued.append(Job(0, 0, params))

    # override
    def _process_jobs_in_queue(self) -> None:
        self.logger.debug(f'_process_jobs_in_queue (q{len(self.queued)}, pr{len(self.in_progress)})')
        # this will prevent scheduling if there is already a job in progress
        if len(self.in_progress) > 0:
            return
        
        # skip resources check!
        i = 0
        while i < len(self.queued):
            # TODO: THIS LOOP IS MALFUNCTIONING. need to adjust indexing after pop. still works tho
            job = self.queued[i]
            new_job = self._start_job(job)
            self.in_progress.append(new_job)
            self.queued.pop(i)
            # this will prevent scheduling if there is already a job in progress
            break 
            i += 1

