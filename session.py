import context
import time

@context.Context
class Session:
    refresh = False
    query = None
    modified = time.time()
    params = {}
    type = 'text/html; charset=utf-8'
    handler = None
