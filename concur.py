from tornado.ioloop import IOLoop

ioloop = IOLoop.instance()

try: import queue
except:
    import Queue as queue
import threading
from six import raise_from
import sys

iolock = threading.RLock()

class Terminator: pass

class RemoteCaller:
    def __init__(self,thread,func):
        self.func = func
        self.thread = thread
    def __get__(self,obj,klass):
        if threading.current_thread() == self.thread:
            return self.func.__get__(obj,klass)
        return lambda *a,**kw: self.fuckit((obj,)+a,kw)
    def __call__(self,*a,**kw):
        return self.fuckit(a,kw)
    def fuckit(self,a,kw):
        return self.thread.schedule(self.func,a,kw)

class Returner(Future):
    def set_exception(self,err):
        ioloop.add_callback(super().set_exception,err)
    def set_result(self,value):
        ioloop.add_callback(super().set_result,err)

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
        super(Thread,self).__init__()
        self.setDaemon(True)
        self.queue = queue.Queue(maxsize)
    def run(self):
        print('runnnn')
        try:
            self.runfoo()
        except:
            import traceback
            traceback.print_exc()
            raise
        finally:
            print('foobarbauaeusnth')
    def runfoo(self):
        while True:
            w = self.queue.get()
            print('got',w)
            if w is Terminator: break
            try:
                if w.returner:
                    print('start',w.f)
                    ret = w.f(*w.a,**w.kw)
                    print('end')
                    w.returner.set_result(ret)
                else:
                    assert w.f(*w.a,**w.kw) is None,str(f)+" shouldn't return a value!"
            except:
                print('derpaderp')
                import traceback
                traceback.print_exc()
                w.returner.set_exc_info(sys.exc_info())
                raise # shouldn't do this
    def schedule(self,f,a,kw):
        if returning:
            returner = Returner()
            self.queue.put(Work(f,a,kw,returner))
            return returner
        else:
            self.queue.put(Work(f,a,kw,None))
    def finish(self):
        self.queue.put(Terminator)
        self.join()

def threadify(k):
    return k # sigh
    thread = Thread(100)
    k.finish = thread.finish
    for n in dir(k):
        f = getattr(k,n)
        if hasattr(f,'threadexport'):
            setattr(k,n,RemoteCaller(thread,f))
    thread.start()
    return k

def export(f):
    f.threadexport = True
    return f

def test():
    import time
    @threadify
    class StupidBlocker:
        @export
        def foo(self):
            time.sleep(1)
            return 'bar'
        @export
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

    @gen
    def coro():
        b = StupidBlocker()
        bar = b.foo()
        print(elapsed(),'foo',bar)
        bar = yield bar
        print(elapsed(),'foo',bar)
        bar = yield b.foo2()
        print(elapsed(),'foo2',bar)
        bar = b.foo3()
        print(elapsed(),'foo3',bar)
        b.finish()
        print(elapsed(),'b done')
    coro()
    ioloop.start()
if __name__ == '__main__':
    test()
