def Context(klass):
    stack = []
    attrs = []
    for n in klass.__dict__.keys():
        if not n.startswith('_'):
            attrs.append(n)
    class Derivate(klass):
        def update(self):
            for n in attrs:
                setattr(Derivate,n,getattr(self,n))
        def __enter__(self):
            stack.append(self)
            self.update()
        def __exit__(self,*a):
            stack.pop(-1).update()
    Derivate.__name__ = klass.__name__
    return Derivate
