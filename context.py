import tracker_coroutine

def methodize(f):
    class Method:
        def __get__(self,cls):
            return f
    return Method

def Classmethodize(klass):
    for n,v in klass.__dict__.items():
        if n == '__dict__': continue
        if hasattr(v,'__call__') or hasattr(v,'__get__'):
            setattr(klass,n,classmethod(v))
    return klass

def Context(klass):
    defaults = dict()
    rest = dict()
    for n,v in klass.__dict__.items():
        if n == '__dict__': continue
        elif n.startswith('_') or hasattr(v,'__call__'):
            rest[n] = v
        else:
            defaults[n] = v
    stacks = {}
        # one stack per coroutine...

    if tracker_coroutine.which in stacks:
        stack = stacks[tracker_coroutine.which]
    else:
        stack = [defaults]
        stacks[tracker_coroutine.which] = stack
        
    # below top the stack must be tuples, so they don't mutate when the top does
    # must push a copy every enter, because even if same "self" must not mutate after exit
    class Derivate: 
        __doc__ = rest.get('__doc__','')
        def __init__(self): pass
        def __enter__(self):
            derps = stack[-1]
            items = tuple(derps.items())
            stack[-1] = items
            stack.append(derps)
        def __exit__(self,*a):
            stack.pop()
            stack[-1] = dict(stack[-1])
        def __getattr__(self,n):
            if n == 'stack': return stack
            elif n in rest: 
                v = rest[n]
            else:
                v = stack[-1][n]
            if hasattr(v,'__get__'):				
                return v.__get__(klass)
            return v
        def __setattr__(self,n,v):
            if n == 'stack':
                setattr(super(),n,v)
                return
            elif n in rest:
                return rest[n]
            stack[-1][n] = v
    for n,v in rest.items():
        if n == '__init__': continue
        try: setattr(Derivate,n,v)
        except AttributeError: pass
    d = Derivate()
    d.__name__ = klass.__name__
    return d

def test():
    @Context
    class Test:
        a = 3
        b = 4
        def foo(self):
            print('sum',self.a,self.b,self.a+self.b)
            return 3

    print(Test.foo())
    with Test:
        Test.a = 5
        print(Test.foo())
        with Test:
            Test.a = 7
            print(Test.foo())
        print(Test.foo())

    print(Test.foo())
if __name__ == '__main__': test()
