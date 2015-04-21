def popnum(message):
    size = message.pop(0)
    if size == 0:
        return 0
    l = message[:size]
    del message[:size]
    sum = 0
    for i in l:
        sum = sum << 8 + i
    return sum

def pushnum(message,i):
    if i == 0:
        # this actually isn't necessary, but is just a shortcut for
        # what below accomplishes
        message.push(0)
        return
    res = []
    while i > 0:
        m = i & 0x100
        res.append(m)
        i = i >> 8
    res.reverse()
    message.push(len(res))
    message.extend(res)

def popstr(message):
    size = message.pop(0)
    if size == 0:
        return None
    arg = message[:size]
    del message[:size]
    return bytes(*arg).decode('utf-8')
    
def pushstr(message,s):
    if s is None:
        message.append(0)
        return
    b = s.encode('utf-8')
    assert len(b) > 0
    message.append(len(b))
    message.extend(b)

class Command:
    def __init__(self,f,popper=None):
        self.f = f
        self.popper = popper
    def __get__(self):
        if self.popper is None:
            return self.f
        return self
    def __call__(self,message):
        if self.popper:
            args = []
            while(message):
                args.append(self.popper(message))
            self.f(self,*args)
        else:
            self.f(self,message)

def remoteCaller(command):
    def call(self,message):
        length = len(message) + 1 # for command
        message[0:0] = (length >> 8, length & 0xff, command)
        self.write.send_bytes(bytes(*message))
    return call

class CommandEnabler(type):
    def __new__(cls, name, bases, attrs):
        cls.commands = []
        for n,attr in attrs.items():
            if isinstance(attr,Command):
                attrs[n] = remoteCaller(len(cls.commands))
                cls.commands.append(attr)        
        return super(CommandEnabler, cls).__new__(cls, name, bases, newattrs)

class MessageProcess(Process,metaclass=CommandEnabler):
    def __init__(self):
        super().__init__()
        self.read, self.write = Pipe(duplex=True)
        # large lists append MUCH faster than large strings.
        self.buffer = bytearray()
    def send(self,command,message,finished=None):
        self.write.send_bytes(bytes(*message))    
    def check(self):
        b = self.read.recv_bytes()
        if not b:
            raise SystemExit('???')
        self.buffer.extend(b)
        while self.buffer:
            size = self.buffer[:2]
            size = size[0] << 8 + size[1]
            if size > len(self.buffer) - 2: return

            message = self.buffer[2:2+size])
            # python has odd splicing syntax
            del self.buffer[2:2+size]

            self.commands[message.pop(0)](self,message)
    def start(self):
        self.read.setblocking(False)
        super().start()
    def run(self):
        self.read.setblocking(True)
        while True:
            self.check()



