from tornado import gen

tracecoroutine = gen.coroutine

class Exit(Exception): pass
