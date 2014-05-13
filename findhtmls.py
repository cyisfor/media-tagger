#!/usr/bin/env pypy3

import os,magic,signal
from bs4 import BeautifulSoup
from gi.repository import Gtk,Gdk,GLib

clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

if hasattr(magic,'from_file'):
    def test(path):
        return magic.from_file(path,mime=true).decode().startswith('text/html')
else:
    magic = magic.open(magic.MIME|magic.NO_CHECK_ENCODING|magic.CONTINUE)
    magic.load()
    def test(path):
        return magic.file(path)

paths = []

def main():
    signal.signal(signal.SIGINT,signal.SIG_DFL)
    for top,dirs,files in os.walk('.'):
        for n in files:
            path = os.path.join(top,n)
            if os.stat(path).st_size > 8192: continue
            if not test(path): continue
            paths.append(path)
    it = iter(enumerate(paths))
    def handleNext():
        try: i,path = next(it)
        except StopIteration:
            Gtk.main_quit()
            return
        print('{:d}/{:d} check'.format(i,len(paths)),path)
        with open(path,'rb') as inp:
            try: doc = BeautifulSoup(inp.read().decode('utf-8'))
            except UnicodeDecodeError: 
                return handleNext()
            try: link = doc.find('a')['href']
            except TypeError:
                print(doc)
            else:
                clipboard.set_text(link,-1)
                print('  ',link)
        dialog = Gtk.Dialog("{:d}/{:d} ".format(i,len(paths))+path,None,0,(Gtk.STOCK_OK,42))
        responded = False
        def gotResponse(dialog,response):
            nonlocal responded
            responded = True
            if response == 42:
                dialog.destroy()
                return handleNext()
            else:
                Gtk.main_quit()
        def gotClose(dialog):
            if responded: return
            Gtk.main_quit()
        dialog.connect('close',gotClose)
        dialog.connect('response',gotResponse)
        dialog.show_all()
    handleNext()
GLib.idle_add(main)
Gtk.main()
