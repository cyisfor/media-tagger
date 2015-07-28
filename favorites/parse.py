#!/usr/bin/env python3
import sys
import os

if len(sys.argv)>1:
    mode = 0
elif 'stdin' in os.environ:
    mode = 1
else:
    mode = 2

if mode == 2:
    try: 
        import pgi
        pgi.install_as_gi()
    except ImportError: pass
print('pgi do')

import syspath
import fixprint
import catchup
from dbqueue import enqueue

if __name__ == '__main__':
    import select
    import settitle
    settitle.set('parse')
    if mode == 0:
        enqueue(sys.argv[1])
        catchup.finish()
    elif mode == 1:
        for line in sys.stdin:
            enqueue(line.strip())
            catchup.poke()
        catchup.finish()
    else:
        def doparsethingy():
            import fcntl,os,time
            from itertools import count
            import gtkclipboardy as clipboardy
            from mygi import Gtk
            def gotPiece(piece):
                print("Trying {}".format(piece.strip()))
                sys.stdout.flush()
                enqueue(piece.strip())
                catchup.poke()
                print("poked")
            print('Ready to parse')
            win = Gtk.Window()
            win.connect('destroy',Gtk.main_quit)
            win.set_title('parse')
            win.show_all()
            clipboardy.run(gotPiece,lambda piece: b'http' == piece[:4])
        if 'ferrets' in os.environ:
            try:
                doparsethingy()
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise SystemExit(23)
        else:
            import os
            os.environ['ferrets'] = 'yep'
            os.environ['name'] = 'parser'
            pid = os.fork()
            os.execlp('daemonize','daemonize',sys.executable,sys.argv[0])
