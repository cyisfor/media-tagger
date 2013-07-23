#!/usr/bin/env python3
import syspath

import catchup
from dbqueue import enqueue

if __name__ == '__main__':
    import select
    import sys
    if len(sys.argv)>1:
        enqueue(sys.argv[1])
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
        clipboardy.run(gotPiece)
        catchup.finish()
