from tornado.gen import Return
import traceback
from contextlib import wraps
try:
    import pygments
    from pygments.lexers.python import Python3TracebackLexer
    from pygments.formatters.terminal256 import Terminal256Formatter
except ImportError as e:
    print(e)
    raise SystemExit
    pygments = None
else:
    tblex = Python3TracebackLexer()
    terminalFormat = Terminal256Formatter()

def derp(): yield
generator = type(derp())
del derp

def printTrace(s):
    if pygments:
        s = pygments.highlight(s,tblex,terminalFormat)
    print(s)

def printTraceIfException(f):
    i = f.exc_info()
    if i:
        printTrace(traceback.format_exception(*i))

def printStack(f):
    @wraps(f)
    def wrapper(*a,**kw):
        noprint = False
        try:
            res = f(*a,**kw)
        except Exception as e:
            printTrace(traceback.format_exc())
            return
        if isinstance(res,generator):
            rr = None
            while True:
                # up
                try: 
                    rr = res.send(rr)
                except StopIteration: break
                # upp
                rr = yield rr
        elif hasattr(res,'add_done_callback'):
            res.add_done_callback(printTraceIfException)
        else:
            raise Return(res)

    return wrapper
                
            
