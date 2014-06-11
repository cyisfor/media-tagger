#!/usr/bin/env python3
import syspath

import catchup
from dbqueue import enqueue

import os

if __name__ == '__main__':
    import select
    import sys
    import settitle
    settitle.set('parse')
    if len(sys.argv)>1:
        enqueue(sys.argv[1])
        catchup.poke()
    elif 'stdin' in os.environ:
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
