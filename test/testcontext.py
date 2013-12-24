import context

class Derp(context.Context):
    a = 3
    @classmethod
    def foo(cls,bar):
        cls.a = bar

import threading

class First(threading.Thread):
    def run(self):
        print('First')
        Derp.foo(1)
        print(Derp.stack)
        with Derp:
            Derp.foo(2)
            with Derp:
                Derp.foo(3)
                print('foo',Derp.a)
            print('bar',Derp.a)

class Second(threading.Thread):
    def run(self):
        print('Second')
        Derp.a -= 1
        print('Derp 42 - 1 = ',Derp.a)

with Derp:
    print('a',Derp.a)
    Derp.foo(23)
    print('b',Derp.a)
    Derp.a = 42

print("back to 3",Derp.a)
print(Derp.stack)
Derp.a = 42

def do(t):
    t = t()
    t.start()
    t.join()
do(First)
print("back to 42",Derp.a)
print(Derp.stack)
do(Second)
