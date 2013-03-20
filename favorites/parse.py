#!/usr/bin/env python3
if __name__ == '__main__':
    import sys,os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parseBase import *
import parsers

if __name__ == '__main__':
    import select
    import sys
    if len(sys.argv)>1:
        parse(sys.argv[1])
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
            tbuf += buf
            pieces = tbuf.split(b'\0')
            if len(pieces)>1:
                for piece in pieces[:-1]:
                    piece = piece.decode('utf-8')
                    thing = next(counter)
                    print('counter',thing)
                    if thing < countdown: continue
                    if 'http' in piece:
                        if alreadyHere(piece):
                            print("WHEN I AM ALREADY HERE")
                            #continue
                        while True:
                            try:
                                parse(piece.strip())
                                break
                            except RuntimeError as e:
                                print(e)
                                break
                            except urllib.error.URLError as e:
                                print(e.getcode(),e.reason,e.geturl())
                                time.sleep(3)
            tbuf = pieces[-1]
