#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        counter = count(1)
        countdown = 0
        stdin = sys.stdin.fileno()
        fl = fcntl.fcntl(stdin, fcntl.F_GETFL)
        fcntl.fcntl(stdin, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        tbuf = b''
        while True:
            select.select([stdin],[],[],None)
            buf = os.read(stdin,0x1000)
            if not buf: break
            print("er",repr(buf))
            tbuf += buf
            pieces = tbuf.split(b'\0')
            if len(pieces)>1:
                for piece in pieces[:-1]:
                    piece = piece.decode('utf-8')
                    thing = next(counter)
                    print('counter',piece,thing)
                    sys.stdout.flush()
                    if thing < countdown: continue
                    if 'http' in piece:
                        print("Trying {}".format(piece.strip()))
                        sys.stdout.flush()
                        enqueue(piece.strip())
                        catchup.poke()
                        print("poked")
            tbuf = pieces[-1]
        catchup.finish()
