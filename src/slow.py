import numpy as np
import time

def fast(n):
    A = np.random.rand(n,n)
    B = np.random.rand(n,n)
    x = np.random.rand(n)
    return np.linalg.norm(A @ B @ x)
    
def slow(n):
    A = np.random.rand(n,n)
    B = np.random.rand(n,n)
    x = np.random.rand(n)
    for i in range(500):
        x = A @ B @ x
    return np.linalg.norm(x)

def eepee(t):
    time.sleep(t)

def main():
    for i in range(10):
        print(f'iter {i}',end='')
        fast(200)
        slow(200)
        eepee(0.1)
        print('.')
    print('done')

if __name__ == "__main__":
    main()
