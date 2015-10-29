import queue,threading

class Terminator: pass

class RemoteCaller:
    def __init__(self,thread,f,wait=False):
        self.f = f
        self.thread = thread
        self.wait = wait
    def __get__(self,obj,klass):
        return lambda *a,**kw: self.fuckit((obj,)+a,kw)
    def __call__(self,*a,**kw):
        return self.fuckit(a,kw)
    def fuckit(self,a,kw):
        return self.thread.schedule(self.f,a,kw,self.wait)

class Returner:
    value = None
    yay = False
    def __init__(self):
        self.condition = threading.Condition()
    def set(self,value):
        self.value = value
        with self.condition:
            self.yay = True
            self.condition.notify_all()
    def get(self):
        with self.condition:
            while not self.yay:
                self.condition.wait()
        return self.value

class Work:
    ticket = 0
    def __init__(self,f,a,kw,returner=None):
        self.f = f
        self.a = a
        self.kw = kw
        self.returner = returner
    def __repr__(self):
        return 'worker for '+repr(self.f)

class Thread(threading.Thread):
    def __init__(self,maxsize=0):
        super().__init__()		
        self.queue = queue.Queue(maxsize)
    def run(self):
        while True:
            w = self.queue.get()
            print('got',w)
            if w is Terminator: break
            if w.returner:
                ret = w.f(*w.a,**w.kw)
                w.returner.set(ret)
            else:
                assert w.f(*w.a,**w.kw) is None,str(f)+" shouldn't return a value!"
    def schedule(self,f,a,kw,returning):
        if returning:
            returner = Returner()
            self.queue.put(Work(f,a,kw,returner))
            return returner.get()
        else:
            self.queue.put(Work(f,a,kw,None),block=False)
    def finish(self):
        self.queue.put(Terminator)
        self.join()
            
def threadify(k):
    thread = Thread(100)
    k.finish = thread.finish
    for n in dir(k):
        f = getattr(k,n)
        if hasattr(f,'threadexport'):
            print(f,hasattr(f,'threadwait'))
            setattr(k,n,RemoteCaller(thread,f,hasattr(f,'threadwait')))
    thread.start()
    return k

def export(wait=True):
    # wait might just be a function so we can do implied @export()
    if wait is True or wait is False:
     def deco(f):
         f.threadexport = True
         if wait:
             f.threadwait = True
         return f
     return deco
    else:
        f = wait
        f.threadexport = True
        f.threadwait = True
        return f

def test():
    import time
    @threadify
    class StupidBlocker:
        @export
        def foo(self):
            time.sleep(1)
            return 'bar'
        @export(wait=False)
        def foo2(self):
            time.sleep(1)
            print("can't return a bar")
        def foo3(self):
            time.sleep(1)
            return 'bar3'

    start = time.time()
    def elapsed():
        e = time.time()-start
        return int(e*10)/10
    
    b = StupidBlocker()
    bar = b.foo()
    print(elapsed(),'foo',bar)
    bar = b.foo2()
    print(elapsed(),'foo2',bar)
    bar = b.foo3()
    print(elapsed(),'foo3',bar)
    b.finish()
    print(elapsed(),'b done')

if __name__ == '__main__':
    test()
    
