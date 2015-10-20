import os,sys
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

here = os.path.dirname(sys.modules[__name__].__file__)
        
def processLocked(reason):
    path = os.path.join(here,".lock-image-tagger-"+reason)
    def deco(f):
        def wrapper(*a,**kw):
            with open(path, 'wb') as lock:
                print('locking for',reason)
                fcntl.lockf(lock, fcntl.LOCK_EX)
                print('locked for',reason)
                try:
                    return f(*a,**kw)
                finally:
                    print('unlocking for',reason)									
        return wrapper
    return deco
