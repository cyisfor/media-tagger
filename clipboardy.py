try: 
    import pgi
    pgi.install_as_gi()
except ImportError: pass

from gi.repository import GLib

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
    def collect(channel,condition,proc):
        nonlocal buf
        status, piece, amt = channel.read_chars()
        if status != GLib.IOStatus.NORMAL: return GLib.SOURCE_REMOVE
        buf += piece
        lines = buf.split('\n')
        buf = lines[-1]
        for line in lines[:-1]:
            if check is None or check(line):
                handler(line)
    proc = s.Popen([exe],stdout=s.PIPE)
    channel = GLib.IOChannel.unix_new(proc.stdout.fileno())
    channel.set_encoding('utf-8')
    GLib.io_add_watch(channel,GLib.PRIORITY_DEFAULT, GLib.IO_IN, collect, proc)

def run(handler, check=None):
    start(handler,check)
    GLib.MainLoop().run()
