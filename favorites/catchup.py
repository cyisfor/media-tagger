#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parseBase import *
import parsers
from dbqueue import top,fail,win
import threading
from db import c
import time
import fixprint

isThreading = True
poked = threading.Condition()

notdone = True

class Catchup(threading.Thread):
    def run(self):
        while notdone:
            print("beep")
            uri = top()
            if uri is None:
                if isThreading:
                    with poked:
                        print("waiting for poke")
                        poked.wait()
                        print("squeak!")
                else:
                    break
                continue
            ah = alreadyHere(uri)
            if ah:
                print("WHEN I AM ALREADY HERE")
            #else:
            try:
                for attempts in range(5):
                    print("Parsing",uri)
                    try:
                        parse(uri)
                        win(uri)
                        break
                    except urllib.error.URLError as e:
                        print(e.getcode(),e.reason,e.geturl())
                        time.sleep(3)
                else:
                    raise RuntimeError("Could not parse",uri)
            except:
                print("fail",uri)
                fail(uri)
                if ah: continue
                import traceback,sys
                traceback.print_exc(file=sys.stdout)
                time.sleep(1)

def poke():
    with poked:
        poked.notifyAll()

started = False
thread = None

def start():
    global thread
    global started
    if started: return
    started = True
    thread = Catchup()
    thread.start()

def finish():
    global notdone
    notdone = False
    poke()
    thread.join()

if __name__ == '__main__':
    isThreading = False
    Catchup().run()
