import os
import fcntl

class Lock:
    def __init__(self, handle):
        self.filename = filename
    # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock 
    def __enter__(self):
        # This will create it if it does not exist already
        fcntl.lockf(self.handle, fcntl.LOCK_EX)        
    def __exit__(self,*a):
        # this will unlock it
        self.handle.close()
        
def processLocked(reason):
    path = "@image/tagger/"+reason
    def deco(f):
        def wrapper(*a,**kw):
            with open(path, 'wb') as lock:
                fcntl.lockf(lock, fcntl.LOCK_EX)
                return f(*a,**kw)
        return wrapper
    return deco
