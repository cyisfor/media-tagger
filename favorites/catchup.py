#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from favorites.parseBase import *
from favorites import parsers
from dbqueue import top,fail,win,megafail,delay,host
from db import c
import db
import clipboardy

import threading
import time
import fixprint

class Catchup(threading.Thread):
    done = False
    def __init__(self):
        super().__init__()
        self.condition = threading.Condition()
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
        except URLError as e:
            if e.getcode() == 503:
                delay(uri,100)            
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
                    self.condition.wait()
        except SystemExit: pass
        except KeyboardInterrupt: pass
    def poke(self):
        with self.condition:
            self.condition.notifyAll()
    def finish(self):
        self.done = True
        while True:
            self.poke()
            self.join(1)
            if not self.isAlive(): break
            self.done = True




instance = Catchup()
instance.start()

poke = instance.poke

finish = instance.finish

if __name__ == '__main__':
    finish()
