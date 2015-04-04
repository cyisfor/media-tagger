#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from favorites.parseBase import *
from favorites import parsers
from dbqueue import top,fail,win,megafail,delay,host
import db

from multiprocessing import Process, Condition
import time
import fixprint

class Catchup(Process):
    done = False
    def __init__(self):
        super().__init__()
        self.condition = Condition()
    def squeak(self,*a):
        uri = top()
        if uri is None:
            print('none dobu')
            if self.done: raise SystemExit
            return
        ah = alreadyHere(uri)
        if ah:
            print("WHEN I AM ALREADY HERE")
        try:
            for attempts in range(2):
                print("Parsing",uri)
                try:
                    parse(uri)
                    win(uri)
                    break
                except urllib.error.URLError as e:
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
        except:
            print("fail",uri)
            fail(uri)
            if not ah:
                import traceback,sys
                traceback.print_exc(file=sys.stdout)
                time.sleep(1)
        return True
    def run(self):
        db.reopen()
        with self.condition:
            self.done = False
        try:
            while True:
                while self.squeak() is True: pass
                with self.condition:
                    if self.done: break
                    print('waiting for pokes')
                    self.condition.wait()
                    print('squeak!')
        except SystemExit: pass
        except KeyboardInterrupt: pass
    def poke(self):
        with self.condition:
            self.condition.notify_all()
    def finish(self):
        self.done = True
        while True:
            self.poke()
            self.join(1)
            if not self.is_alive(): break
            self.done = True




instance = Catchup()

if __name__ == '__main__':
    instance.squeak()
else:
    instance.start()

    poke = instance.poke

    finish = instance.finish
