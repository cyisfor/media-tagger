#!/usr/bin/env python3
import sys
import os

myself = os.path.abspath(sys.modules[__name__].__file__)
here = os.path.dirname(myself)

if len(sys.argv)>1:
    mode = 0
elif 'stdin' in os.environ:
    mode = 1
else:
    mode = 2
    if not 'ferrets' in os.environ:
        os.environ['ferrets'] = 'yep'
        os.environ['name'] = 'parser'
        os.execlp('daemonize',
                  'daemonize',sys.executable,os.path.abspath(myself))

import syspath
import fixprint
from dbqueue import enqueue

if __name__ == '__main__':
    import catchup
    if mode == 0:
        enqueue(sys.argv[1])
    elif mode == 1:
        import settitle
        settitle.set('parse')
        import catchup
        for line in sys.stdin:
            enqueue(line.strip())
            catchup.poke()	
    else:
        def doparsethingy():
            import fcntl,os,time
            from itertools import count
            import gtkclipboardy as clipboardy
            from mygi import Gtk
            print('loading UI')
            ui = Gtk.Builder.new_from_file(os.path.join(here,"parseui.xml"))
            print('boop')
            import catchup
            def gotPiece(piece):
                print("Trying {}".format(piece.strip().replace('\n',' ')[:90]))
                sys.stdout.flush()
                enqueue(piece.strip())
                catchup.poke()
                print("poked")
            print('Ready to parse')
            win = ui.get_object("top")
            def seriouslyQuit(win,e):
                print("Gettin' outta here!",e.button,dir(e.button))
                Gtk.main_quit()
                catchup.terminate()
                raise SystemExit
            win.connect("button-release-event",seriouslyQuit)
            win.connect('destroy',Gtk.main_quit)
            win.set_title('parse')
            win.show_all()
            print('Okay!')
            clipboardy.run(gotPiece,lambda piece: b'http' == piece[:4])
            print('done yay',os.getpid())
        try:
            doparsethingy()
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise SystemExit(23)
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
    print('finishing')
    catchup.finish()
    print('finished')
