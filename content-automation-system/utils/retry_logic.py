import time
import functools
from typing import Callable, Tuple, Type


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 5,
    max_delay: float = 300,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Exponential back-off retry decorator.

    Delays: base_delay * 2^attempt, capped at max_delay.
    Raises the last exception when all retries are exhausted.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"[retry {attempt}/{max_retries}] {func.__name__} failed: {exc} — retrying in {delay:.0f}s")
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
