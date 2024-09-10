import pandas as pd
from glob import glob
import os
import re

def get_peak_mem(mem_df: pd.DataFrame, mem_field='uss'):
    # group and sum by time
    # find max val
    return mem_df.groupby('time')[mem_field].sum().max()

def get_execution_time(mem_df: pd.DataFrame):
    return mem_df.tail(1)['time'].item()

def get_execution_status(err_log_file: str):
    err_re = re.compile('Interrupt|Traceback|ERROR|Error|error')
    ok_re = re.compile('saving finished to')
    
    with open(err_log_file, 'r') as f:
        logtxt = f.read()
    
    has_err = not (err_re.search(logtxt) is None)
    is_ok = not (ok_re.search(logtxt) is None)
    
    if has_err == is_ok:
        return "???"
    if has_err:
        return "ERR"
    return "OK"

def main(benchplan_file: str, results_dir: str, skip_unknown_runs: bool =True, inplace: bool = True):
    """
    Read benchplan, parse results_dir, fill benchplan with results parsed from result_dir.  
    Make sure run labels match log file names in result_dir.

    @param benchplan_file: str, parse according to this benchplan csv
    @param results_dir: str, search for time and mem results in this dir
    @params skip_unknown_runs: bool, default True, do not add run to the results if it is not in the benchplan
    @params inplace: bool, default True, shall we edit the benchplan, or create a new one? If False, output will be at "results_{benchplan_basename}"
    """
    print("Parsing ", benchplan_file, " with results directory ", results_dir, ".")

    df = pd.read_csv(benchplan_file, index_col='run_label')
    df['result_ok'] = df['result_ok'].astype(str)
    files = glob('mem_*.log', root_dir=results_dir)
    offset_l, offset_r = len('mem_'), len('.log')

    print(f"Read {len(df)} runs, found {len(files)} files")

    for file in files:
        log_filename = os.path.join(results_dir, file)
        label = file[offset_l:-offset_r]
        print(label, end='')

        if skip_unknown_runs and label not in df.index:
            print(" skip")
            continue

        try:
            mem_df = pd.read_csv(log_filename)
            print('.', end='')
            result_mem = get_peak_mem(mem_df, mem_field='uss') / 1e6    # Megabytes
            result_time = get_execution_time(mem_df)
            print('.', end='')
            errlog_file = log_filename.replace('.log', '.err')
            result_ok = get_execution_status(errlog_file)
            print('.', end='')
        except Exception as e:
            print(f"skip - error while parsing {log_filename}: ", e)
            continue

        df.loc[label, 'result_mem'] = result_mem
        df.loc[label, 'result_time'] = result_time
        df.loc[label, 'result_ok'] = result_ok
    
        print(result_ok)

    benchplan_basename = os.path.basename(benchplan_file)
    if inplace:
        print("inplace = True therefore adding data to the original benchplan")
        output_path = benchplan_file
    else:
        output_path = f'results_{benchplan_basename}'

    print("Writing results to ", os.path.realpath(output_path))

    df.to_csv(output_path, index=True)
    
    print("Done")


if __name__ == "__main__":
    import fire
    fire.Fire(main)
