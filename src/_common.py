import os
from dataclasses import dataclass, fields
import dataclasses
from typing import Type, Union

"""
"""

from _config import config


"""
"""

def get_field_names(dataclass_or_instance):
    return [f.name for f in fields(dataclass_or_instance)]

"""
"""

@dataclass
class RunnerParams:
    run_label: str

class Runner:
    # static field
    params_class: Type[RunnerParams] = RunnerParams

    @staticmethod
    def get_argv(params: RunnerParams) -> list[str]:
        return []

    @staticmethod
    def get_cwd(params: RunnerParams) -> str:
        dir = os.path.join(config.workdir_root, params.run_label)
        os.makedirs(dir, exist_ok=True)
        return dir

    @staticmethod
    def main():
        pass

"""
"""
