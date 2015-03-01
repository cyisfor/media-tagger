# why did tornado.gen delete sleep?

from tornado.ioloop import IOLoop
from tornado.concurrent import Future

def sleep(secs,ioloop=None):
    if ioloop is None:
        ioloop = IOLoop.current()
    f = Future()
    ioloop.add_timeout(secs,lambda: f.set_result(None))
    return f
    
