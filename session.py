from context import contextify
import time

@contextify
class Session:
    refresh = False
    query = None
    modified = time.time()
    params = {}
    type = 'text/html; charset=utf-8'
    handler = None
    head = False
    prefetching=False
