from functools import wraps
def override(klass,member):
    old = getattr(klass,member)
    def decorator(f):
        @wraps(old)
        def wrapper(self,*a,**kw):
            return f(self,old,*a,**kw)
        setattr(klass,member,wrapper)
    return decorator
