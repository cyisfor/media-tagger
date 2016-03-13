import note

from tornado.concurrent import is_future, Future
from tornado.gen import Return
from tornado.ioloop import IOLoop
from tornado import stack_context
from itertools import count
import sys

nums = count(0)
which = None

def tracker(f):
    def wrapper(*a,**kw):
        global which
        old = which
        try:
            which = wrapper.mine
            gen = f(*a,**kw)
            val = None
            while True:
                # up				
                try: val = gen.send(val)
                except StopIteration: break
                # down
                val = yield val
                which = wrapper.mine
        finally:
            which = old
    wrapper.mine = next(nums)
    return wrapper

def coroutine(ff):
    f = tracker(ff)
    def wrapper(*a,**kw):
        gen = f(*a,**kw)
        done = Future()
        def next_one(val=None):
            while True:
                #note.yellow(f.mine,'gensend',ff,val)
                try: val = gen.send(val)
                except StopIteration:
                    #note.yellow(f.mine,'gendone',ff,val)
                    done.set_result(None)
                    return
                except Return as e:
                    note.yellow(f.mine,"excretval",e.value,done.running())
                    done.set_result(e.value)
                    note.shout("foop")
                    assert not done.running()
                    return
                except:
                    #note.yellow("exn",sys.exc_info())
                    done.set_exception(sys.exc_info()[1])
                    gen.throw(*sys.exc_info())
                    return
                if is_future(val): break
                note.alarm('uhhh',val)
                done.set_result(val)
                return
            #note.yellow(f.mine,"fuval",val._callbacks)
            assert is_future(val), val
            @stack_context.wrap
            def call_next_one(fu):
                try:
                    note.yellow(f.mine,"fuvaldone",fu.result())
                    next_one(fu.result())
                except:
                    note.red(f.mine,"fuvalexn",sys.exc_info()) 
                    done.set_exception(sys.exc_info()[1])
                    gen.throw(*sys.exc_info())
            IOLoop.instance().add_future(val,call_next_one)
        next_one()
        return done
    return wrapper
