import traceback
try:
    import pygments
    from pygments.lexers.python import Python3TracebackLexer
    from pygments.formatters.terminal256 import Terminal256Formatter
except ImportError:
    tblex = None
else:
    tblex = Python3TracebackLexer()
    terminalFormat = Terminal256Formatter

def printStack(f):
    def wrapper(*a,**kw):
        try: res = f(*a,**kw)
        except Exception as e:
            s = traceback.format_exc()
            if pygments:
                s = pygments.highlight(s,tblex,terminalFormat)
            print(s)
                
            
