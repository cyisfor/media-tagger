import threading

def methodize(f):
    class Method:
        def __get__(self,cls):
            return f
    return Method

def makeContext():
    # we can't just return the Operations class
    # because it has a different metaclass than Meta!
    class Meta(type):
        def __enter__(self):
            self.stack.append(dict(self.stack[-1].items()))
        def __exit__(self,*a):
            self.stack.pop()
        def __getattr__(self,name):
            if name == 'stack':
                return self.__dict__['stack']
            return self.stack[-1][name]
        def __setattr__(self,name,value):
            if name == 'stack':
                setattr(super(),name,value)
                return
            self.stack[-1][name] = value
        def __new__(cls,name,bases,dct):
            d = dict()
            methods = dict()
            for n,v in dct.items():                
                if not n.startswith('_'):
                    if hasattr(v,'__call__') or \
                        hasattr(v,'__get__'):
                            # don't bother pushing/popping methods
                        methods[n] = v
                    else:
                        d[n] = v
            class State:
                lastStack = {}
                def __repr__(self):
                    self.check()
                    return repr(id(self.state.stack))
                def __init__(self):
                    self.state = threading.local()
                def check(self):
                    if not hasattr(self.state,'stack'):
                        self.state.stack = (self.lastStack,)
                    self.lastStack = dict(self.state.stack[-1].items())
                def __getitem__(self,i):
                    self.check()
                    return self.state.stack[i]
                def append(self,v):
                    self.check()
                    self.state.stack += (v,)
                def pop(self):
                    self.check()
                    self.state.stack = self.state.stack[:-1]
            methods['stack'] = State()
            self = type.__new__(cls,name,bases,methods)
            self.stack.append(d)            
            return self

    class Context(metaclass=Meta): pass
    return Context

Context = makeContext()
