import time
from concurrent.futures import ThreadPoolExecutor
import functools

from logger import logger


def retry(num_retries, wait_seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(num_retries):
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    if i == num_retries - 1:
                        raise e
                    else:
                        logger.error(repr(e))
                        time.sleep(wait_seconds)
                else:
                    return result
        return wrapper
    return decorator

class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message='Function call timed out'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except TimeoutError:
                    future.cancel()
                    raise TimeoutError(error_message)
        return wrapper
    return decorator
