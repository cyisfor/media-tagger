from tornado.ioloop import IOLoop
from tornado.concurrent import Future

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
    def __init__(self,thread,func,returning):
        self.func = func
        self.thread = thread
        self.returning = returning
    def __get__(self,obj,klass):
        if threading.current_thread() == self.thread:
            return self.func.__get__(obj,klass)
        return lambda *a,**kw: self.fuckit((obj,)+a,kw)
    def __call__(self,*a,**kw):
        return self.fuckit(a,kw)
    def fuckit(self,a,kw):
        return self.thread.schedule(self.func,a,kw,self.returning)

class Returner(Future):
    def set_exception(self,err):
        ioloop.add_callback(super().set_exception,err)
    def set_result(self,result):
        ioloop.add_callback(super().set_result,result)

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
            print('thread shutting down')
    def runfoo(self):
        while True:
            w = self.queue.get()
            if w is Terminator: break
            try:
                if w.returner:
                    ret = w.f(*w.a,**w.kw)
                    w.returner.set_result(ret)
                else:
                    assert w.f(*w.a,**w.kw) is None,str(f)+" shouldn't return a value!"
            except:
                w.returner.set_exc_info(sys.exc_info())
                continue
    def schedule(self,f,a,kw,returning=True):
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
    thread = Thread(100)
    k.finish = thread.finish
    for n in dir(k):
        f = getattr(k,n)
        if hasattr(f,'threadexport'):
            setattr(k,n,RemoteCaller(thread,f,f.threadreturning))
    thread.start()
    return k

def export(returning=True):
    if returning is True or returning is False:
        def deco(f):
            f.threadreturning = returning
            f.threadexport = True
            return f
        return deco
    # allow implied returning
    f = returning
    f.threadreturning = True
    f.threadexport = False
    return f

def test():
    import time
    @threadify
    class StupidBlocker:
        @export
        def foo(self):
            time.sleep(1)
            print('foo!')
            return 'bar'
        @export(returning=False)
        def foo2(self):
            time.sleep(1)
            print("foo2 can't return a bar")
        def foo3(self):
            time.sleep(1)
            print('foo3!')
            return 'bar3'

    start = time.time()
    def elapsed():
        e = time.time()-start
        return int(e*10)/10

    from tornado.gen import coroutine
    @coroutine
    def coro():
        b = StupidBlocker()
        bar = b.foo()
        print(elapsed(),'foo',bar,'(0 elapsed)')
        # no time elapses until you wait on the future!
        bar = yield bar
        print(elapsed(),'foo',bar,'(1 elapsed)')
        bar = b.foo2()
        print(elapsed(),'foo2',bar,'(still 1 elapsed)')
        # functions that don't return (returning=False) return None, not a future
        b.finish()
        print(elapsed(),'b done','(about 2 elapsed)')
        # however, it will wait until all functions are done before finishing
        
        bar = b.foo3()
        print(elapsed(),'foo3',bar,'(2 elapsed)')
        # normal functions are just that, not in the thread
        # XXX: could error out if called not from within the thread?
        # boo, that's C++ style encapsulation.

        ioloop.stop()
    coro()
    ioloop.start()
if __name__ == '__main__':
    test()
