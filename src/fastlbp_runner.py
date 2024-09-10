import numpy as np
from skimage.io import imread
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from typing import Union
from dataclasses import dataclass
import os

import fastlbp_imbg as fastlbp

from _config import config
from _common import Runner, RunnerParams

"""
"""

@dataclass
class FastlbpBenchplanRecord:
    run_label: str
    input_shape: tuple[int,int,int]
    input_tiff_path: str
    mask_npy_path: str
    mask_ratio: float
    patchsize: int
    ncpus: int
    nradii: int
    approx_mem_usage_gb: int

    repeat: int = 1

    # results
    result_time: float = None
    result_mem: float = None
    result_ok: str = None


@dataclass
class FastlbpRunnerParams(RunnerParams):
    # run_label: str from RunnerParams
    input_tiff_file: str
    mask_npy_path: str
    patchsize: int
    ncpus: int
    nradii: int


class FastlbpRunner(Runner):
    # static field
    params_class = FastlbpRunnerParams

    @staticmethod
    def get_argv(params: FastlbpRunnerParams):
        argv = [ config.fastlbp_pybin, os.path.join(config.src_root, 'fastlbp_runner.py') ]
        argv += [ params.run_label, params.input_tiff_file, str(params.mask_npy_path), str(params.patchsize), str(params.ncpus), str(params.nradii)]
        return argv
    
    @staticmethod
    def main(run_label: str, input_tiff_path: str, mask_npy_path: Union[str, None], patchsize: int, ncpus: int, nradii: int):
        """
        A single Fastlbp run
        
        :param run_label: unique ID of this run
        :param input_tiff_path: path to tiff
        :param mask_npy_path: path to mask in npy format or `None` if no mask is needed
        :param patchsize: patchsize lbp param
        :param ncpus: ncpus lbp param
        :param nradii: calculate lbp using first `nradii` radiuses from default radii list (see fastlbp.get_radii) with default npoints (fastlbp.get_p_for_r)
        """
        assert fastlbp.__version__ == "0.1.4"
        assert input_tiff_path.endswith(".tiff")
        assert mask_npy_path is None or mask_npy_path=="" or mask_npy_path=="None" or mask_npy_path.endswith(".npy")
        
        print("Reading input file")
        print("mask_npy_path is ", mask_npy_path)
        
        img_data = imread(input_tiff_path)
        
        use_mask = False
        mask_data = None
        if mask_npy_path is not None and len(mask_npy_path)>0 and mask_npy_path != "None":
            use_mask = True
            print("Reading mask")
            mask_data = np.load(mask_npy_path)
        
        radii_list = fastlbp.get_radii(nradii)
        npoints_list = fastlbp.get_p_for_r(radii_list)

        print("Starting fastlbp")
        
        output_abs_path, effective_mask = fastlbp.run_fastlbp(
            img_data, radii_list, npoints_list, 
            patchsize, 
            ncpus=ncpus, 
            outfile_name=f"{run_label}_output.npy",  # output file name, will be in the ./data/out
            img_name=run_label,    # human-friendly name, optional
            save_intermediate_results=False,  # do not use cache
            overwrite_output=True,     # no error if output file already exists,
            img_mask=mask_data
        )

"""
"""

def fastlbp_benchplan_to_runner(benchplan_record: FastlbpBenchplanRecord) -> FastlbpRunnerParams:
    r = benchplan_record
    return FastlbpRunnerParams(
        r.run_label, 
        r.input_tiff_path if r.input_tiff_path else '', 
        r.mask_npy_path if r.mask_npy_path else '', 
        r.patchsize, 
        r.ncpus, 
        r.nradii
    )

"""
"""

if __name__ == "__main__":
    import fire
    fire.Fire(FastlbpRunner.main)
