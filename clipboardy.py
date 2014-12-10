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

def run(handler,check=None):
    proc = s.Popen([exe],stdout=s.PIPE)
    while True:
        num = proc.stdout.readline().decode('utf-8')
        try: amt = int(num,0x10)
        except ValueError:
            print('num?',num)
            return
        text = proc.stdout.read(amt)
        if check:
            res = check(text)
            if res is not True:
                text = res
        if text and not text in seen:
            seen.add(text)
            if type(text) == bytes:
                text = text.decode('utf-8',errors='replace')
            handler(text)
        time.sleep(0.2)
