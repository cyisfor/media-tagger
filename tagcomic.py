import comic
import tags

import os,sys

nt = tags.parse(os.environ['tags'])

prefix = 'http://[fcd9:e703:498e:5d07:e5fc:d525:80a6:a51c]/art/~comic/'.encode()
def gotPiece(piece):
    print('trying',piece)
    try: c = int(piece[len(prefix):].split('/',1)[0],0x10)
    except ValueError: raise
    print('comic',c,nt)
    comic.tag(c,nt)

def nerp():
    print('enter tago')
    for line in sys.stdin:
        gotPiece(line)

import gtkclipboardy as clipboardy
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
clipboardy.run(gotPiece, lambda piece: piece[:len(prefix)] == prefix) 
