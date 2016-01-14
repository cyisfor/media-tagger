import threading,queue
from mygi import GLib

bgqueue = queue.Queue()
def background(f):
    bgqueue.push(f)

def foreground(f):
    GLib.idle_add(f)

@threading.Thread
def bgThread():
    import comic,db
    from favorites.parseBase import parse, ParseError, normalize
    import favorites.parsers # side effects galore!
    bgqueue.put(True)
    while True:
        try:
            try: g,backToforeground = result
            except ValueError:
                # eh, just a function, will do its own foregrounding
                result()
                continue
            for mode in g:
                if mode is foreground:
                    GLib.idle_add(backToforeground)
                    return
        except:
            import traceback
            traceback.print_exc()
            print('background thread exception!!')
bgqueue.get() # okay stuff is imported and connected to db IN THE BACKGROUND

def dually(f):
    def wrapper(*a,**kw):
        g = f(*a,**kw)
        def inGUI():
            for mode in g:
                if mode is background:
                    bgqueue.push(g,inGUI)
                    return
        inGUI()
