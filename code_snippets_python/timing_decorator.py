import time
from functools import wraps

def timeit(method):
    @wraps(method)
    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()
        print('Timer (s): ', te - ts)
        return result
    return timed