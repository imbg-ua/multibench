from dataclasses import dataclass
import os

@dataclass
class Config:
    """
    General
    """

    # Absolute path to src directory.
    # Must be set manually!
    src_root = "Y:/multibench/src"

    # Absolute path to a dir containing working directories.
    # Workdir for a job will be "${workdir_root}/${job_name}".
    # Must be set manually!
    workdir_root = "Y:/multibench/workdir"

    # Absolute path.
    # Pipeline will search for input files (images and masks) here.
    # Must be set manually!
    input_dir = "Y:/multibench/input"

    # Absolute path.
    # Job results and stats will be placed in this dir.
    # Must be set manually!
    results_dir = "Y:/multibench/results"

    """
    FastlbpRunner
    """

    # An absolute path to python executable that will run fastlbp. 
    # Usually it is a path to conda executable ('/path/to/env/bin/python')
    fastlbp_pybin = 'python'

    """
    System
    """

    # RAM of your PC
    max_mem_gb = 16

    # Numbers of CPUs in your PC = number of physical cores
    max_ncpus = 4

config = Config()
