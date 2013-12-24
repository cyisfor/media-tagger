import multiprocessing
from itertools import count
import time
    
def serve_forever(makeServer):
    class Derp:
        def _handle_request_noblock(self): pass
    makeServer = lambda: Derp()

    pool = multiprocessing.Pool(processes=10)
    def one_request(i):
        server = makeServer()
        for i in range(200):
            server._handle_request_noblock()
    while True:
        print('boop')
        pool.map(one_request,range(40))
