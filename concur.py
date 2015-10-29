import queue,threading

class RemoteCaller:
    def __init__(self,thread,f,wait=False):
        self.f = f
        self.thread = thread
        self.wait = wait
    def __call__(self,*a,**kw):
        self.thread.schedule(self.f,a,kw,self.wait)

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

class Thread(threading.Thread):
    def __init__(self,maxsize=0):
        self.queue = queue.Queue(maxsize)
    def run(self):
        while True:
            w = self.queue.get()
            if w.returner:
                ret = w.f(*w.a,**w.kw)
                w.returner.set(ret)
            else:
                assert(w.f(*w.a,**w.kw) is None,str(f)+" shouldn't return a value!")
    def schedule(self,f,a,kw,returning):
        if returning:
            returner = Returner()
            self.queue.put(Work(f,a,kw,returner))
            return returner.get()
        else:
            self.queue.put(Work(f,a,kw,None))
            
def threadify(k):
    thread = Thread()
    for n in dir(k):
        f = getattr(k,n)
        if(hasattr(f,'threadexport'):
            setattr(k,n,RemoteCaller(thread,f),hasattr(f,'threadwait'))

def export(wait=True):
    def deco(f):
        f.threadexport = True
        if wait: f.threadwait = True
        return f
