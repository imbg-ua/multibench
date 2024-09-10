import numpy as np
from multiprocessing import Process
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager
from time import sleep, perf_counter

"""
memtest v1

Launch several parallel processes with shared memory to test the profiler.
"""

def fill_memory(size_mb: int, base2: bool = True):
    if base2:
        return np.ones((size_mb, 1024, 1024), dtype=np.uint8)
    else:
        return np.ones((size_mb, 1000, 1000), dtype=np.uint8)

def child(t0, child_number, shared_mem, child_mem_mb, shared_shape, write_to_shared: bool):
    print(f"{perf_counter()-t0:.3f}: c{child_number}: get shared data")
    # shared_data = np.ndarray(shared_shape, np.uint8, shared_mem.buf)
    shared_data = np.frombuffer(shared_mem.buf, np.uint8).reshape(shared_shape)
    sleep(0.5)

    if write_to_shared:
        print(f"{perf_counter()-t0:.3f}: c{child_number}: writing to shared mem")
        shared_data[child_number] = shared_data[child_number] * 2
        sleep(0.5)

    print(f"{perf_counter()-t0:.3f}: c{child_number}: child data")
    child_data = fill_memory(child_mem_mb)
    sleep(0.5)

    print(f"{perf_counter()-t0:.3f}: c{child_number}: exiting ({child_data.sum()/1e6}, {shared_data.sum()/1e6})")
    return

def main(main_mem_mb:int = 200, child_mem_mb: int = 100, shared_mem_mb:int = 500, n_children:int = 4, write_to_shared:bool = True):
    t0 = perf_counter()
    
    print(f"{perf_counter()-t0:.3f}: Main data")
    main_data = fill_memory(main_mem_mb)

    sleep(0.5)

    print(f"{perf_counter()-t0:.3f}: data to share")
    data_to_share = fill_memory(shared_mem_mb)

    with SharedMemoryManager() as smm:
        print(f"{perf_counter()-t0:.3f}: shared memory")
        shared_mem = smm.SharedMemory(data_to_share.size)
        shared_data = np.ndarray(data_to_share.shape, data_to_share.dtype, shared_mem.buf)
        np.copyto(shared_data, data_to_share)
        sleep(0.5)

        print(f"{perf_counter()-t0:.3f}: remove data to share")
        del data_to_share
        sleep(0.5)

        print(f"{perf_counter()-t0:.3f}: Start children")
        children = [ Process(target=child, args=(t0, i, shared_mem, child_mem_mb, shared_data.shape, write_to_shared)) for i in range(n_children) ]
        for cp in children:
            cp.start()
        for cp in children:
            cp.join()

        print(f"{perf_counter()-t0:.3f}: Children done")
        sleep(0.5)
    
        print(f"{perf_counter()-t0:.3f}: Remove shared memory ({shared_data.sum()/1e6})")
    sleep(0.5)

    print(f"{perf_counter()-t0:.3f}: Exiting ({main_data.sum()/1e6})")
    return

if __name__ == "__main__":
    import fire
    fire.Fire(main)
