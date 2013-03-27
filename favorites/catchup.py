from parseBase import *
import parsers
from dbqueue import top,dequeue
import threading
from db import c

poked = threading.Condition()

notdone = True

class Catchup(threading.Thread):
    def run(self):
        while notdone:
            uri = top()
            if uri is None:
                with poked:
                    poked.wait()
                continue
            if alreadyHere(uri):
                print("WHEN I AM ALREADY HERE")
            else:
                while True:
                    try:
                        parse(uri)
                        break
                    except RuntimeError as e:
                        print(e)
                        break
                    except urllib.error.URLError as e:
                        print(e.getcode(),e.reason,e.geturl())
                        time.sleep(3)
            dequeue(uri)

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
