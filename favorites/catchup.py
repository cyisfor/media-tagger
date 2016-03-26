#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from favorites.parseBase import *
from favorites import parsers
from dbqueue import top,fail,win,megafail,delay,host
import db

from multiprocessing import Process, Condition, Value
import time
import fixprint

from ctypes import c_bool

class Catchup(Process):
    def __init__(self):
        super().__init__()
        self.condition = Condition()
        self.done = Value(c_bool,False)
    def run(self):
        db.reopen()
        try:
            import signal
            signal.signal(signal.SIGUSR1, lambda sig: None)
            while True:
                while self.squeak() is True: pass
                with self.condition:
                    if self.done.value: break
                    print('waiting for pokes')
                    self.condition.wait()
                    print('squeak!')
        except SystemExit: pass
        except KeyboardInterrupt: pass
    def squeak(self,*a):
        uri = top()
        if uri is None:
            print('none dobu')
            if self.done.value: raise SystemExit
            return
        ah = alreadyHere(uri)
        if ah:
            print("WHEN I AM ALREADY HERE")
            if 'noupdate' in os.environ:
                win(uri)
                return True
        try:
            for attempts in range(2):
                print("Parsing",uri)
                try:
                    parse(uri)
                    win(uri)
                    break
                except urllib.error.URLError as e:
                    print(e.headers)
                    print(e.getcode(),e.reason,e.geturl())
                    if e.getcode() == 404: raise ParseError('Not found')
                    time.sleep(3)
            else:
                print("Could not parse",uri)
        except ParseError:
            print('megafail')
            megafail(uri)
        except urllib.error.URLError as e:
            if e.getcode() == 503:
                print('site is bogged down! delaying a while')
                delay(uri,'1 minute')
            print('megafail error',e.getcode())
            megafail(uri)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                print('uhm, forbid?')
            print(e,dir(e))
            raise SystemExit(23)
        except Exception as e:
            print("fail",uri,e)
            raise SystemExit(23)
            fail(uri)
            if not ah:
                import traceback,sys
                traceback.print_exc(file=sys.stdout)
                time.sleep(1)
        return True

class Catchupper:
    def __init__(self):
        self.process = Catchup()
        self.process.start()
    def poke(self):
        with self.process.condition:
            if not self.process.is_alive():
                print('died?')
                self.process = Catchup()
                self.process.start
            self.condition.notify_all()
    def finish(self):
        self.process.done.value = True
        while True:
            self.poke()
            self.process.join(1)
            if not self.is_alive(): break
            self.process.done.value = True


if __name__ == '__main__':
    instance = Catchup()
    while instance.squeak() is True: pass
else:
    instance = Catchupper()

    poke = instance.poke
    terminate = instance.process.terminate
    finish = instance.finish
