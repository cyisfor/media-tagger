import os

class Command: pass

class MessagePutter:
    def __init__(self,name,command,q):
        self.name = name
        self.codec = command.codec
        self.codecs = command.codecs
        self.queue = q
    def __call__(self,*a,**kw):
        if not (self.codec or self.codecs):
            message, = a
            self.q.put(message) #uhhhgghghg

class Proxy(Process):
    def __init__(self,template):
        super().__init__()
        self.q = m.Queue()
        for n in dir(template):
            v = getattr(template,n)
            if isinstance(v,Command):
                setattr(self,n,MessagePutter(n,v,q))
                # don't need to leave Command wrapper
                # after detected
                setattr(template,n,v.f)
        self.template = template
    def setProxies(proxies):
        self.proxies = proxes
    def run():
        while True:
            try: self.template(*self.proxies)
            except (KeyboardInterrupt,SystemExit):
                break
            except Exception:
                import traceback
                print('====== ',self.pid,file=sys.stderr)
                traceback.print_exc()
    
                
def go(*runners):
    proxies = []*len(runners)
    for i,runner in enumerate(runners):        
        proxies[i] = Proxy(runner)
    for i,proxy in enumerate(proxies[:-1]):
        proxy.setProxies(proxies[:i]+proxies[i+1:])
        proxy.start()
    proxy = proxies[-1]
    proxy.setProxies(proxies[:-1])
    proxy.run()
