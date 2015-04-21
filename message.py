class codecs:
    class num:
        @staticmethod
        def decode(message):
            size = message.pop(0)
            if size == 0:
                return 0
            l = message[:size]
            del message[:size]
            sum = 0
            for i in l:
                sum = sum << 8 + i
            return sum
        @staticmethod
        def encode(message,i):
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

    class str:
        @staticmethod
        def decode(message):
            size = message.pop(0)
            if size == 0:
                return None
            arg = message[:size]
            del message[:size]
            return bytes(*arg).decode('utf-8')

        @staticmethod
        def encode(message,s):
            if s is None:
                message.append(0)
                return
            b = s.encode('utf-8')
            assert len(b) > 0
            message.append(len(b))
            message.extend(b)
    class onestr:
        @staticmethod
        def decode(message):
            s = bytes(*message).decode('utf-8')
            message[:] = ()
            return s
        @staticmethod
        def encode(message,s):
            message[:] = s.encode('utf-8')

class Command:
    codecs = None
    def __init__(self,f,command,codec=None,codecs=None):
        self.f = f
        self.command = command
        if codecs:
            self.codecs = codecs
        else if codec:
            self.codecs = [codec]
    def __get__(self):
        if self.codecs is None:
            return self.f
        return self
    def __call__(self,message):
        if self.codecs:
            args = []
            i = 0
            while(message):
                codec = self.codecs.get(i)
                if codec is None:
                    codec = self.codecs[0]
                args.append(codec.decode(message))
                i = i + 1
            self.f(self,*args)
        else:
            self.f(self,message)
    def __remotelycall__(self,proc,*args):
        message = [0,0,self.command]
        if self.codecs:
            for i,arg in enumerate(args):
                codec = self.codecs.get(i)
                if codec is None:
                    codec = self.codecs[0]
                codec.encode(message,arg)
        else:
            message.extend(args[0])
        length = len(message) + 1 # for command
        message[0:2] = (length >> 8, length & 0xff)
        self.write.send_bytes(bytes(*message))

class CommandEnabler(type):
    def __new__(cls, name, bases, attrs):
        cls.commands = []
        for n,attr in attrs.items():
            if hasattr(attr,'__remotelycall__'
                attrs[n] = attr.__remotelycall__
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
