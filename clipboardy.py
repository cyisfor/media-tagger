import coro

from tornado import ioloop,gen
from tornado.process import Subprocess

import time
import subprocess as s
import sys,os

here = os.path.dirname(sys.modules[__name__].__file__)

exe = os.path.join(here,"xwatch-0.1/xclipwatch")

if not os.path.exists(exe):
    pid = os.fork()
    if pid == 0:
        os.chdir(os.path.join(here,"xwatch-0.1"))
        s.call(["./configure"])
        os.execlp("make","make")
    os.waitpid(pid)

seen = set()


@coro.tracecoroutine
def start(handler,check=None):
    buf = b''
    proc = Subprocess([exe],stdout=Subprocess.STREAM)
    while True:
        print('getting line')
        length = yield proc.stdout.read_until(b'\n')
        line = yield proc.stdout.read_bytes(int(length,0x10))
        if check is None or check(line):
            handler(line.decode('utf-8'))

def run(handler, check=None):
    start(handler,check)
    ioloop.IOLoop.instance().start()
