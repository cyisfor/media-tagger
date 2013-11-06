raise RuntimeError("This is dumb. use peak.context instead")
class obj(object):
    stack = []
    def __init__(self, **d):
        self.__dict__['__d'] = d
    def get(self,n):
        return self.__dict__['__d'].get(n)
    def __getattr__(self,n):
        if n == '__d': return object.__getattr__(self,n)
        return self.__dict__['__d'][n]
    def __getitem__(self,n):
        return self.__dict__['__d'][n]
    def __setattr__(self,n,v):
        if n == '__d': return object.__setattr__(self,n,v)
        self.__dict__['__d'][n] = v
    def __delattr__(self,n):
        del self.__dict['__d'][n]
    def __enter__(self):
        obj.stack.append(self.__dict__['__d'].items())
        return self
    def __exit__(self,*a):
        self.__dict__['__d'].update(obj.stack.pop())

