import threading,queue
def makeWorker(init,foreground):
    bgqueue = queue.Queue()
    def background(f):
        bgqueue.put(f)

    initcond = threading.Condition()
    initted = False
        
    def bgThread():
        nonlocal initted
        init()
        with initcond:
            initted = True
            initcond.notify_all()
        while True:
            try:
                result = bgqueue.get()
                try: g,backToForeground = result
                except (TypeError,ValueError) as e:
                    # eh, just a function, will do its own foregrounding
                    print(result,e)
                    result()
                    continue
                for mode in g:
                    if mode is foreground:
                        foreground(backToForeground)
                        return
            except:
                import traceback,time
                traceback.print_exc()
                print('background thread exception!!')
                time.sleep(1)
    threading.Thread(target=bgThread,daemon=True).start()
    while True:
        with initcond:
            initcond.wait()
            if initted: break
        
    def dually(f):
        def wrapper(*a,**kw):
            g = f(*a,**kw)
            def inForeground():
                for mode in g:
                    if mode is background:
                        bgqueue.put((g,inForeground))
                        return
            inForeground() # XXX: ok to assume in foreground?
        return wrapper
    return dually,background
