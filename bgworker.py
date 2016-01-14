import threading,queue
def makeWorker(init,foreground):
    bgqueue = queue.Queue()
    def background(f):
        bgqueue.push(f)

    @threading.Thread
    def bgThread():
        init()
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
    return dually,background
