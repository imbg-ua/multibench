import os
from config_values import config

def ensure_config_ok():
    print("=== benchmarking-beta config ===")
    print("Current working directory = ", os.getcwd())
    print("src_root =", config.src_root)
    print("workdir_root =", config.workdir_root)
    print("input_dir =", config.input_dir)
    print("results_dir =", config.results_dir)
    print("======")

    def ensure_dir_exists(name, path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                raise IOError(f"Cannot create '{name}' directory at {path} - file already exists")
        else:
            print(f"Directory '{name}' does not exist. Making {path}")
            os.makedirs(path, exist_ok=True)

    ensure_dir_exists('workdir_root', config.workdir_root)
    ensure_dir_exists('results_dir', config.results_dir)
