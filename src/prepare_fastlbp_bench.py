from _benchplan import FastlbpBenchplan
from _config import config

# bench plan file path
bench_plan_path = './bench_plan.csv'

"""
CONFIG: test cases

Bench plan consists of all possible combinations of the following parameters
"""

all_shapes = [
    (1000,1000,1),
    (1000,1000,3),
]

all_maskratio = [0, 0.5]

all_patchsize = [100]

all_ncpus = [1,2,4]

all_nradii = [5,10]


"""
END CONFIG
"""

if __name__ == "__main__":
    bp = FastlbpBenchplan()
    bp.add_combinations_fastlbp(
        all_shapes,
        all_maskratio,
        all_patchsize,
        all_ncpus,
        all_nradii
    )
    bp.save(bench_plan_path)
