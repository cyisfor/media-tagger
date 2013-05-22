import fcntl,select,os

def readClipmon(inp,gotPiece,sep=None):
    if sep is None:
        sep = os.environ.get('sep','\0')
    sep = sep.encode('utf-8')
    inp = inp.fileno()
    fl = fcntl.fcntl(inp, fcntl.F_GETFL)
    fcntl.fcntl(inp, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    tbuf = b''
    done = False
    while True:
        select.select([inp],[],[],None)
        buf = os.read(inp,0x1000)
        if not buf: done = True
        else: tbuf += buf
        pieces = tbuf.split(sep)
        if len(pieces)>1 or done:
            if done: section = pieces
            else: section = pieces[:-1]
            for piece in section:
                gotPiece(piece.decode('utf-8'))
            if not done: tbuf = pieces[-1]
        if done: break
