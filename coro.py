import note
note.monitor(__name__)

import tracker_coroutine
from tornado import gen
from tornado.concurrent import Future
from functools import wraps
import traceback
import sys

class Exit(Exception): pass

def tracecoroutine(f):
    @wraps(f)
    def wrapper(*a,**kw):
        g = f(*a,**kw)
        thing = None
        try:
            if not(hasattr(g,'send')):
                note('nogen?',f)
                return
            while True:
                thing = g.send(thing)
                try: thing = yield thing
                except Exception as e:
                    note('ex down',type(e))
                    thing = g.throw(e)
        except StopIteration: pass
        except gen.Return as e: 
            # why this isn't default, no idea.
            value = e.value
            while gen.is_future(value):
                value = yield value
            raise gen.Return(value)
        except Exit:
            raise
        except:
            note.alarm('error in ',f)
            traceback.print_exc()
            return
    return tracker_coroutine.coroutine(wrapper)

success = Future()
success.set_result(42)
