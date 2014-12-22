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

buf = b''
def collect(channel,condition,proc):
    global buf
    status, piece, amt = channel.read_chars()
    if status != GLib.IOStatus.NORMAL: return GLib.SOURCE_REMOVE
    buf += piece

def run(handler,check=None):
    proc = s.Popen([exe],stdout=s.PIPE)
    channel = GLib.unix_new(proc.stdout.fileno())
    channel.set_flags(GLib.IOFlags.NONBLOCK)
    GLib.io_add_watch(channel,GLib.PRIORITY_DEFAULT, GLib.IO_IN, collect, proc)
