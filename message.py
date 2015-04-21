class OneToMany:
    def __init__(self,one):
        self.one = one
    def decode(self,message):
        size = message.pop(0)
        if size == 0:
            return 0
        l = message[:size]
        del message[:size]
        return self.one.decode(l)
    def encode(self,message,v):
        if not v:
            # this actually isn't necessary, but is just a shortcut for
            # what below accomplishes
            message.push(0)
            return
        res = bytearray()
        self.one.encode(res)
        message.push(len(res))
        message.extend(res)
        del res[:]
        
class codecs:
    class one:
        class str:
            @staticmethod
            def decode(message):
                s = bytes(*message).decode('utf-8')
                return s
            @staticmethod
            def encode(message,s):
                message[:] = s.encode('utf-8')
        class num:
            @staticmethod
            def decode(message):
                sum = 0
                for i in message:
                    sum = sum << 8 + i
                return sum
            @staticmethod
            def encode(message,i):
                while i > 0:
                    m = i & 0x100
                    message.append(m)
                    i = i >> 8
                message.reverse()
    str = OneToMany(one.str)
    num = OneToMany(one.num)
    
class Command:
    codec = None
    command = None
    def __init__(self,f,codec=None,codecs=None,backend=False):
        self.backend = backend
        self.f = f
        self.codecs = codecs
        if codec:
            self.codec = codec
        elif 'default' in codecs:
            self.codec = codecs.pop('default')
    def __get__(self):
        return self
    def remotely_called(self,commander,message):
        if self.codecs:
            args = []
            i = 0
            while(message):
                if self.codecs:
                    codec = self.codecs.get(i)
                    if codec is None:
                        codec = self.codec
                else:
                    codec = self.codec
                args.append(codec.decode(message))
                i = i + 1
            self.f(commander,*args)
        else:
            self.f(commander,message)
    def __call__(self,commander,*args):
        if commander.backend is self.backend:
            # no state transition, just call it!
            return self.f(commander,*args)
        # send to the other side, which will call its self.f
        # later.
        assert self.command is not None
        message = [0,0,self.command]
        for i,arg in enumerate(args):
            if self.codecs:
                codec = self.codecs.get(i)
                if codec is None:
                    codec = self.codec
            else:
                codec = self.codec
            codec.encode(message,arg)
        else:
            message.extend(args[0])
        length = len(message) + 1 # for command
        message[0:2] = (length >> 8, length & 0xff)
        self.write.send_bytes(bytes(*message))

class CommandEnabler(type):
    commands = []
    def __new__(cls, name, bases, attrs):
        for n,attr in attrs.items():
            if isinstance(attr,Command):
                attr.command = len(CommandEnabler.commands)
                # all commands must have global IDs
                # so no subclasses w/ separate lists!
                cls.commands = CommandEnabler.commands
                CommandEnabler.commands.append(attr)
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

            self.commands[message.pop(0)].remotely_called(self,message)
    backend = False
    def start(self):
        self.read.setblocking(False)
        super().start()
    def run(self):
        self.backend = True
        self.read.setblocking(True)
        while True:
            self.check()
