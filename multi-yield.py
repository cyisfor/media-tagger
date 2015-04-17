from itertools import count
def counte():
    for i in range(3):
        a = yield i
        print('a',a)
def relay(gs):
    result = None
    g = gs.pop()
    while True:
        try:
            result = g.send(result)
        except StopIteration:
            print('this result failed to send needs to be sent again',result)
            if not gs: break
            g = gs.pop()
            derp = next(g)
            print('this is the first result from the next generator',derp)
            derp2 = yield derp
            print('input for derp',derp,derp2)
            derp3 = g.send(result)
            print('sending the result above',result,'gives',derp3)
            derp4 = yield derp3
            print('input for derp3',derp3,derp4)
            derp5 = g.send(derp4)
            derp6 = yield derp5
            print('derp56',derp5,derp6)
            # etc...
            result = derp6
        else:
            result = yield result

b = relay([counte(),counte(),counte()])
print(',',next(b))
while True:
    print(',',b.send('a'))
    print(',',b.send('b'))
    print(',',b.send('c'))
    print(',',b.send('d'))
    print(',',b.send('e'))
    print(',',b.send('f'))
raise SystemExit
def inner():
    print('in 1')
    a = yield 42
    print('in 2',a,a+42)
    yield a + 42

def outer():
    print('out 1')
    a = yield inner()
    print('out 2',a,a+43)
    yield a + 43

g = outer()
print(dir(g))
forme = next(g)
forme2 = next(forme)
forthem = forme.send(forme2 - 99)
final = g.send(forthem)
print('final',final)

'''
So here's the idea
use yield instead of return and NEVER just 'return'
all generators must yield at least once
that way when you f() can be sure it'll be a generator
and when you next(g) if it returns a generator means more input is needed.
when it does not, means final result, to be passed up to parent generators

if next(g) yields a generator, that becomes a child generator of g, and its final result must then be passed to g.
'''

sterile = set()
def nochild(f):
    def wrapper(*a,**kw):
        g = f(*a,**kw)
        assert(type(g) == generator)
        sterile.add(g)
        return g
    return wrapper

class Want:
    def __init__(self,g):
        self.g = g
        self.send = g.send
        self.__next__ = g.__next__
    def __getattr__(self,n):
        return getattr(self.g,n)

@nochild
def inner():
    print('in 1')
    a = yield 42
    print('got a',a)
    a = a or 0
    b = yield a+23
    print('got b',b)
    b = b or 0
    print('in 2',a,b,(a+b+42))
    yield a + b + 42

def outer():
    print('out 1')
    a = yield inner()
    a = a or 0
    print('out 2',a,a+43)
    yield a + 43

def foo():
    yield 42
generator = type(foo())
del foo
print(generator)

sentinel = []

def drain(g):
    stack = []
    result = None
    while True:
        if isinstance(result,generator):
            if result in sterile:
                sub = None
                while True:
                    print('passing down',sub,result)
                    try: sub = result.send(sub)
                    except StopIteration: 
                        print('already sent',sub,'so can drop it')
                        break
                    else:
                        sub = yield sub
                print('result for inner',result,sub)
                result = sub # final result
            else:
                print('pushing',g,result)
                stack.append(g)
                g = result
                result = next(g)
                print(result)
                continue
        # now result is not a generator
        try: 
            print('sending to level',g,result)
            result = g.send(result)
        except StopIteration:
            if stack:
                print('popping generator',g,result)
                g = stack.pop(-1)
            else:
                print('finally',result)
                yield result
                return

def outer2():
    a = yield outer()
    b = yield outer()
    yield a + b

g = drain(outer2())
print('!!',next(g))
for i in count(0):
    try:
        print('>>',i,g.send(i))
    except StopIteration:
        print('stopped at',i)
        break

