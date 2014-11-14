from tornado.concurrent import Future, is_future
import sys

def assureFuture(val):
    if is_future(val): return val
    future = Future()
    future.set_result(val)
    return future

def drain(ioloop,g):
    # g yields possibly futures, and finally raises Return a result
    # or the last result it yielded is the final result

    # when g yields a future it is in the form of a = yield future
    # where a is intended to be the result of the future
    # so must send the result of the future back to g when it's ready

    # passthrough functions that need the result of g but don't themselves yield futures
    # should have the following form:
    #
'''
        g = something(...)
        result = None
        while True:
            # pull from below
            try:
                result = g.send(result)
            except StopIteration: break
            except gen.Return as ret:
                result = ret.value
                break
            # pull from above
            result = yield result
'''

    # they can also call drain(ioloop,g) and add a callback to the resulting future.

    # drain itself has the above form, but deals with the result as a possible future
    # instead of yielding it.

    # Can't have turtles all the way down after all.

    # note done callback return values are silently dropped
    # must set_result in a second future to have a return value    
    done = Future()

    # note a = g.send(None) is equivalent to a = next(g)
    
    def once(result=None):
        try:
            result = g.send(result)
        except Return as ret:
            done.set_result(ret.value)
            return
        except StopIteration:
            # result was not set in the above expression, so it's the last result yielded still
            done.set_result(ret.value)
            return

        if is_future(result):
            # the result of the future must be sent back to g
            # but we can't go back to once() again right away
            ioloop.add_future(result, once)
            return
    once()
    return done

