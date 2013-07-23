#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parseBase import *
import parsers
from dbqueue import top,fail,win
from db import c
import clipboardy

from gi.repository import GLib, Gtk, Gdk
import time
import fixprint

derpwhat = False

class Catchup:
    def __init__(self):
        self.notdone = True
    def squeak(self,*a):
        print("DERP",a)
        uri = top()
        if uri is None:
            if derpwhat: Gtk.main_quit()
            return
        print("squeak!")
        ah = alreadyHere(uri)
        if ah:
            print("WHEN I AM ALREADY HERE")
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
            if not ah:
                import traceback,sys
                traceback.print_exc(file=sys.stdout)
                time.sleep(1)
        GLib.idle_add(self.squeak)

instance = Catchup()

def poke():
    GLib.idle_add(instance.squeak)

if __name__ == '__main__':
    derpwhat = True
    poke()
    Gtk.main()
