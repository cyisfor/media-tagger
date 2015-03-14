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
        catchup.poke()
    elif mode == 1:
        for line in sys.stdin:
            enqueue(line.strip())
        catchup.poke()
    else:
        import fcntl,os,time
        from itertools import count
        import clipboardy
        def gotPiece(piece):
            if 'http' in piece:
                print("Trying {}".format(piece.strip()))
                sys.stdout.flush()
                enqueue(piece.strip())
                catchup.poke()
                print("poked")
        print('Ready to parse')
        clipboardy.run(gotPiece)
    catchup.finish()
