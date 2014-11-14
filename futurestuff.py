from tornado.concurrent import Future, is_future
import sys

def assureFuture(val):
    if is_future(val): return val
    future = Future()
    future.set_result(val)
    return future

def stackdepth():
    n = 1
    frame = sys._getframe(1)
    while frame:
        n = n + 1
        frame = frame.f_back
    return n

def drain(ioloop,g):
    # g yields possibly futures, and finally raises Return a result
    # or the last result it yielded is the final result

    # when g yields a future it is in the form of a = yield future
    # where a is intended to be the result of the future
    # so must send the result of the future back to g when it's ready

    # passthrough functions that need the result of g but don't themselves yield futures
    # should have the following form:
    #
    # result = next(g)
    # while is_future(result):
    #     result = yield result
    #     result = g.send(result)

    # they can also call drain(ioloop,g) and add a callback to the resulting future.

    # drain itself cannot have that form because it has to return a future, and not be a
    # generator. Can't have turtles all the way down after all.

    # note a = g.send(None) is equivalent to a = next(g)
    
    # note done callback return values are silently dropped
    # must set_result in a second future to have a return value    
    done = Future()

    bottom = stackdepth()
    threshold = sys.getrecursionlimit() - bottom - 0x20

    def once(result=None, level=1):
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
            ioloop.add_future(result, once)
        else:
            # not a future, so can be passed directly to the next iteration
            # ...unless the stack is full. Then trampoline!
            # but how much space to leave for functions that assume there's stack space?
            # 0x20 should be enough...?

            # note if drain calls drain, the second drain will have a higher stack bottom
            # so still won't stack smash

            if level >= threshold:
                ioloop.add_callback(once, result)
            else:
                result = once(result, level+1)
    once()
    return done

