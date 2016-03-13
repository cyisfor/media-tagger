from eventlet.greenthread import sleep
from eventlet.green import subprocess as s

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


def start(handler,check=None):
    buf = b''
    proc = s.Popen([exe],stdout=s.PIPE)
    while True:
        try:
            length = proc.stdout.readline()
            line = yield proc.stdout.read_bytes(int(length,0x10))
            if check is None or check(line):
                handler(line.decode('utf-8'))
        except Exception as e:
            print("ERROR",e)
            yield sleep(1)

def run(handler, check=None):
    start(handler,check)
