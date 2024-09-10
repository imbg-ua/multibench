from src._scheduler import SequentialScheduler
from src._common import Runner, RunnerParams

class TestRunnner(Runner):
    def main():
        pass

    def get_argv(*_):
        return [ "ping", "-n", "4", "127.0.0.1" ]
    

if __name__ == "__main__":
    scheduler = SequentialScheduler(TestRunnner, 8, 16, 1, 1)
    scheduler.add_job(2, 2, RunnerParams('a'))
    scheduler.add_job(4, 4, RunnerParams('b'))
    scheduler.add_job(8, 8, RunnerParams('c'))
    scheduler.add_job(10, 10, RunnerParams('d'))
    scheduler.run()


