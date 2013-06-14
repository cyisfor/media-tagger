import fcntl,select,os

def readClipmon(inp,gotPiece,sep=None,glib=None):
    if sep is None:
        sep = os.environ.get('sep','\0')
    sep = sep.encode('utf-8')
    inp = inp.fileno()
    fl = fcntl.fcntl(inp, fcntl.F_GETFL)
    fcntl.fcntl(inp, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    derp = [b'']
    import inspect
    if glib:
        source = None
    def readSome(*a):
        tbuf = derp[0]
        done = False
        if glib:
            buf = inp.read(0x1000)
            if not buf:
                done = True
        else:
            buf = os.read(inp,0x1000)
            if not buf: done = True
        if not done:
            derp[0] += buf
        pieces = tbuf.split(sep)
        if len(pieces)>1 or done:
            if done: section = pieces
            else: section = pieces[:-1]
            for piece in section:
                gotPiece(piece.decode('utf-8'))
            if not done: derp[0] = pieces[-1]
        if done:
            if glib:
                glib.source_remove(source)
                import gtk
                gtk.gtk_main_quit()
            else:
                raise SystemExit
    if glib:
        inp = glib.IOChannel.unix_new(inp)
        source = glib.io_add_watch(inp,glib.IO_IN|glib.IO_HUP,readSome)
    else:
        while True:
            select.select([inp],[],[],None)
            readSome()
