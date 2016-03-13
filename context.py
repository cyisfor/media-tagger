# thank you so much Aaron Griffith

import parameterize
import eventlet.greenthread
import greenlet
# normally parameterize is set to work with threading locals
# we can simulate this in green threads, with a dictionary lookup by
# thread ID

def derp(value):
    return list(value.items())

env_by_thread = {}
class ThreadLocal:
    def __getattr__(self,name):
        assert(name=='dynamic_environment')
        me = eventlet.greenthread.getcurrent()
        if me in env_by_thread:
            return env_by_thread[me]
        raise AttributeError("no environment")
    def __setattr__(self,name,value):
        assert(name=='dynamic_environment')
        me = eventlet.greenthread.getcurrent()
        env_by_thread[me] = value
        # must set this, since parameterize checks dir(self)
        # to see if the attribute exists...
    def __dir__(self):
        me = eventlet.greenthread.getcurrent()
        if me in env_by_thread:
            return ['dynamic_environment']
        return []

parameterize.set_context_locals(ThreadLocal())

# a coroutine-local-ish stack of contexts
# like implicit arguments passed with every function
# that act like globals

def contextify(klass):
    # klass contains defaults, but what actually is here is a parameter
    # dict, that you lookup with getattr to get/set current values
    # or use call and 'with' to parameterize by copy of current value
    d = dict((n,v) for n,v in klass.__dict__.items() if not n.startswith('_'))
    p = parameterize.Parameter(d)
    class Context:
        def __call__(self):
            d = dict(p.get())
            return p.parameterize(d)
        def __getattr__(self,n):
            return p.get()[n]
        def __setattr__(self,n,v):
            p.get()[n] = v
        __name__ = klass.__name__
    return Context()


def test():
    @contextify
    class Test:
        a = 3
        b = 4
        def foo():
            print('sum',Test.a,Test.b,Test.a+Test.b)
            return 23-Test.a

    print(Test.foo())
    with Test():
        Test.a = 5
        print(Test.foo())
        with Test():
            Test.a = 7
            print(Test.foo())
        print(Test.foo())

    print(Test.foo())

    @greenlet.greenlet
    def thing1():
        with Test():
            Test.a = 5
            print('Test.a is 5')
            thing2.switch()
            print('Test.a is still 5? ',Test.a)
    @greenlet.greenlet
    def thing2():
        with Test():
            Test.a = 23
            print('o noes')
            thing1.switch()
    thing1.switch()

if __name__ == '__main__': test()
