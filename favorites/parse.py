#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    # sigh...
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readclipmon import readClipmon
import catchup
from dbqueue import enqueue

if __name__ == '__main__':
    import select
    import sys
    catchup.start()
    if len(sys.argv)>1:
        enqueue(sys.argv[1])
        catchup.poke()
        catchup.finish()
    else:
        import fcntl,os,time
        from itertools import count
        def gotPiece(piece):
            if 'http' in piece:
                print("Trying {}".format(piece.strip()))
                sys.stdout.flush()
                enqueue(piece.strip())
                catchup.poke()
                print("poked")
        readClipmon(sys.stdin,gotPiece)
        catchup.finish()
