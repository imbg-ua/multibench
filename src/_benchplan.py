from collections import namedtuple
import numpy as np
import os
import fastlbp_imbg as fastlbp
import itertools
import pandas as pd
import re

from _config import config, ensure_config_ok
from _common import get_field_names
from fastlbp_runner import FastlbpBenchplanRecord

def shape2str(shape):
    return "x".join(map(str,shape))

def get_run_label(input_shape, mask_ratio, patchsize, ncpus, nradii, repeat=None):
    rep_str = ""
    if repeat:
        rep_str = f"__{repeat}"
    return f"{shape2str(input_shape)}_m{mask_ratio:.3f}_p{patchsize}_n{ncpus}_r{nradii}" + rep_str

def get_approx_mem_usage_gb(input_shape: tuple[int], mask: bool, patchsize: int, ncpus: int, nradii: int) -> int:
    """
    Returns an approximate memory usage in GB
    """
    # all calculations are in bytes. byte = 8 bit.
    
    # divide first, multiply second, to avoid int32 overflow
    gb = 1e9

    # worst case: uint8 saved as int64 or float64
    input_size = (np.prod(input_shape) / gb) * 8
    # worst case: uint8 saved as int64 or float64
    mask_size = (np.prod(input_shape[:2]) / gb) * 8 if mask else 0
    # always uint16 in my implementation
    lbp_output_size = (np.prod(input_shape) / gb) * 2
    
    # always uint32 in my implementation
    n_features_single_channel = (fastlbp.get_p_for_r(fastlbp.get_radii(nradii))+2).sum() 
    n_channels = input_shape[2]
    feature_array_size = input_size/(patchsize*patchsize) * n_features_single_channel * n_channels * 4

    est_mem_gb = (input_size + mask_size + lbp_output_size + feature_array_size)
    # just in case
    est_mem_gb = est_mem_gb * 1.2
    # round up to nearest gb
    est_mem_gb = np.ceil(est_mem_gb)

    assert est_mem_gb > 0, f"{input_shape}, {mask}, {patchsize}, {ncpus}, {nradii}; {input_size}, {feature_array_size}, {(input_size + mask_size + lbp_output_size + feature_array_size)}"
    return int(est_mem_gb)

def create_disk_mask(img_shape, area=0.5):
    """
    Create mask of a disk shape in the center of the image with ones inside and zeros outside.  
    Size of the disk is such that num_ones_in_mask/num_image_pixels = area.  

    - area parameter should be less than 0.78 ~ pi/4 in order for the disk to fit in the image.
    - if area is 1, then create a mask full of ones (np.ones).
    - if area is None or 0 or 0.0, return None.  
        For further steps that means compute the whole image, do not use mask at all.  
        Note that it differs from the mask full of ones.
    """
    
    if area == 0 or area == 0.0 or area is None:
        return None
    
    mask_shape = img_shape
    if len(img_shape) == 3:
        mask_shape = mask_shape[:2]
    area1 = round(area,3)
    mask_id = shape2str(mask_shape) + f"_{area1:.3f}"
    mask_name = f"{mask_id}.npy"
    mask_path = os.path.abspath(f"{config.input_dir}/{mask_name}")
    
    if os.path.isfile(mask_path):
        # mask exists
        print(f"Mask {mask_id} exists")
        return mask_path
    
    
    print(f"Creating mask {mask_id}...")

    if area > 0.99:
        mask = np.ones(mask_shape, np.uint8)
    elif area > 0.78:
        raise NotImplementedError("Sorry, create_disk_mask only supports disks that fit into the image, i.e. mask_ratio < pi/4 ~ 0.78")
    else:
        h,w = mask_shape[0], mask_shape[1]
        center = (int(h/2), int(w/2))
        axi = np.arange(h) - center[0]
        axj = np.arange(w) - center[1]
        xx,yy = np.meshgrid(axi,axj, sparse=True)
        
        # n_mask_pixels = pi*r2
        # area_ratio = pi*r2 / npixels
        # r2 = npixels * area_ratio / pi
        r2 = float(np.prod(mask_shape) * area1) / np.pi
        mask = ((xx*xx + yy*yy) < r2).astype(np.uint8)
    
    assert mask.shape == mask_shape
    assert mask.dtype == np.uint8
    assert np.abs(mask.mean() - area1) < 0.01
    
    print(f"Saving mask {mask_path}")
    np.save(mask_path, mask)
    
    return mask_path

"""
"""

class FastlbpBenchplan:
    all_runs: list[FastlbpBenchplanRecord]

    def __init__(self):
        self.all_runs = []

    def add_single_fastlbp_run(self, 
                               input_shape: tuple[int, int, int], 
                               mask_ratio: float, 
                               patchsize: int, 
                               ncpus: int, 
                               nradii: int
                               ):
        label = get_run_label(input_shape, mask_ratio, patchsize, ncpus, nradii)

        rec = FastlbpBenchplanRecord(
            run_label= label,
            input_shape= input_shape,
            input_tiff_path= fastlbp.create_sample_image(*input_shape, dir=config.input_dir),
            mask_npy_path= create_disk_mask(input_shape, mask_ratio),
            # input_shape=input_shape,
            mask_ratio=round(mask_ratio,3),
            patchsize= patchsize, 
            ncpus= ncpus, 
            nradii= nradii,
            approx_mem_usage_gb= get_approx_mem_usage_gb(input_shape, (mask_ratio or mask_ratio>0), patchsize, ncpus, nradii)
        )
        
        nrepeat = 1
        pattern = re.compile(rec.run_label)
        for r in self.all_runs:
            if pattern.match(r.run_label) is not None:
                nrepeat += 1
        rec.repeat = nrepeat
        rec.run_label += f'__{nrepeat}'

        self.all_runs.append(rec)

    def add_combinations_fastlbp(self, 
                 shape: list[tuple[int, int, int]],
                 maskratio: list[float],
                 patchsize: list[int],
                 ncpus: list[int],
                 nradii: list[int]
                 ):
        all_params = (shape, maskratio, patchsize, ncpus, nradii) # order is important 
        n = 0
        for single_run_params in itertools.product(*all_params):
            self.add_single_fastlbp_run(*single_run_params)
            n+=1
        print(f"Addded {n} runs.")
    
    # first values will be a baseline
    def add_star_combinations_fastlbp(self, 
                 shape: list[tuple[int, int, int]],
                 maskratio: list[float],
                 patchsize: list[int],
                 ncpus: list[int],
                 nradii: list[int]
                 ):
        all_params = (shape, maskratio, patchsize, ncpus, nradii) # order is important 
        baseline_parameters = [shape[0], maskratio[0], patchsize[0], ncpus[0], nradii[0]]
        n = 0
        for param_id, param_list in enumerate(all_params):
            single_run_params = baseline_parameters.copy()
            for param_value in param_list:
                single_run_params[param_id] = param_value
                self.add_single_fastlbp_run(*single_run_params)
                n+=1
        print(f"Addded {n} runs.")

    def to_df(self):
        df = pd.DataFrame(self.all_runs, columns=get_field_names(FastlbpBenchplanRecord))

        # deduplicate runs with the same parameters - add run number at the end of the label
        num_of_repeat = df.groupby('run_label').cumcount().add(1)
        df['repeat'] = num_of_repeat
        df['run_label'] = np.where(
            df['run_label'].duplicated(keep=False), 
            df['run_label'] + '__' + num_of_repeat.astype(str),
            df['run_label']
        )
        return df

    def save(self, file: str):
        # df = pd.DataFrame(self.all_runs, columns=[
        #     'run_label', 
        #     'input_shape',
        #     'input_tiff_path', 
        #     'mask_npy_path', 
        #     'mask_ratio',  
        #     'patchsize', 
        #     'ncpus', 
        #     'nradii', 
        #     'approx_mem_usage_gb'
        #     ])
        # df['result_time'] = None
        # df['result_mem'] = None
        # df['result_ok'] = ''

        self.to_df().to_csv(file, index=False)

def __normalize_path_field(path):
    assert isinstance(path, str) or path == np.nan, f"invalid path: '{path}' of type {type(path)}"
    if not path or path in [np.nan, 'nan', 'none', 'None', 'null']: return ''
    return path

def read_fastlbp_benchplan(file: str, ensure_runnable=False):
    """
    Create a benchplan object from CSV file without validation.  
    That is, a benchplan could be unusable (e.g. wrong paths, invalid run labels)

    Use ensure_runnable=True to ensure all paths (input files and masks) are valid,
    create the masks and random input files if needed,
    and validate the labels.

    if ensure_runnable=True, all labels are ignored!
    """
    if ensure_runnable:
        ensure_config_ok()

    bp = FastlbpBenchplan()
    # keep_default_na=False prevents filling fields with float(nan) and keeps empty strings instead
    df = pd.read_csv(file, keep_default_na=False)
    for rec in df.itertuples(index=False):
        input_shape = rec.input_shape
        if '(' in rec.input_shape:
            input_shape = rec.input_shape.strip()[1:-1].strip()
        delim = 'x' if 'x' in input_shape else ','
        parsed_shape = tuple(map(lambda s: int(s.strip()), input_shape.split(delim)))
        if ensure_runnable:
            bp.add_single_fastlbp_run(
                parsed_shape,
                rec.mask_ratio,
                rec.patchsize,
                rec.ncpus,
                rec.nradii
                )
        else:
            # print("X: ", rec.mask_npy_path)
            # print("X: ", __normalize_path_field(rec.mask_npy_path))

            params = FastlbpBenchplanRecord(
                rec.run_label, 
                parsed_shape, 
                rec.input_tiff_path, 
                __normalize_path_field(rec.mask_npy_path), 
                rec.mask_ratio,
                rec.patchsize, 
                rec.ncpus, 
                rec.nradii,
                rec.approx_mem_usage_gb,
                rec.repeat,
                rec.result_time,
                rec.result_mem,
                rec.result_ok
                )
            bp.all_runs.append(params)

    return bp
