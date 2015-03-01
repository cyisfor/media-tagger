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

def printStack(f):
    @wraps(f)
    def wrapper(*a,**kw):
        try:
            res = f(*a,**kw)
            return res
        except Exception as e:
            s = traceback.format_exc()
            if pygments:
                s = pygments.highlight(s,tblex,terminalFormat)
            print(s)
    return wrapper
                
            
