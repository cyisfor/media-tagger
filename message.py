from multiprocessing import Process

def oneToMany(one):
    '''
1: size
n: {item}
1: size
n: {item}
...
'''
    #fsck metaclasses
    
    class many(type):
        __name__ = 'many '+one.__name__
        __doc__ = "a list of "+one.__doc__+ oneToMany.__doc__.format(item=one.__name__)
        @staticmethod
        def decode(message):
            size = message.pop(0)
            if size == 0:
                return one.nothing
            l = message[:size]
            del message[:size]
            return one.decode(l)
        @staticmethod
        def encode(message,v):
            if not v:
                # this actually isn't necessary, but is just a shortcut for
                # what below accomplishes
                message.append(0)
                return
            res = bytearray()
            one.encode(res,v)
            message.append(len(res))
            message.extend(res)
            del res[:]
    class o(metaclass=many):
        __doc__ = many.__doc__
        __name__ = 'many '+one.__name__    
    return o
class codecs:
    '''
encode: push arguments encoded to the message
decode: take bytes out of the message and return as value
(decode MAY not clear message (no need if there's only one argument))
'''
    class nothing:
        @staticmethod
        def encode(message,s):
            return message
        @staticmethod
        def decode(message): pass
    class one:
        'only one argument per message'
        class str:
            'bytes of an utf-8 encoded string'
            nothing = ''
            @staticmethod
            def decode(message):
                s = bytes(message).decode('utf-8')
                return s
            @staticmethod
            def encode(message,s):
                message[:] = s.encode('utf-8')
        class num:
            'digits of a number in base 0x100'
            nothing = 0
            @staticmethod
            def decode(message):
                sum = 0
                for i in message:
                    sum = (sum << 8) + i
                return sum
            @staticmethod
            def encode(message,i):
                while i > 0:
                    m = i & 0xff
                    message.append(m)                    
                    i = i >> 8
                message.reverse()
    # strings can't be more than 0xff BYTES long (in utf-8)
    # if you keep within 0-0x80 characters (7-bit) you get 0xff characters
    # 0x80-0x800 eat 2 bytes though, 0x800->0x8000 eat 3, etc
    # using one.str you can have a string up to 0xffff bytes long
    str = oneToMany(one.str)
    num = oneToMany(one.num)
    
class Command:
    codec = None
    command = None
    def __init__(self,f,codec=None,codecs=None,backend=False):
        # if backend is true, this will go to the backend
        # if it's already in the backend, it'll stay there.
        # if it's not, no error, but remotely call
        # and vice versa if backend == false
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
        # this is a pretty safe assumption
        assert self.backend == commander.backend
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
            # if codec == None allow undecoded tails here?
            codec.encode(message,arg)
        else:
            message.extend(args[0])
        length = len(message) + 1 # for command
        message[0:2] = (length >> 8, length & 0xff)
        self.write.send_bytes(message)

def command(**kw):
    def wrapper(f):
        return Command(f,**kw)
    return wrapper
        
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
        return super(CommandEnabler, cls).__new__(cls, name, bases, attrs)

class MessageProcess(Process,metaclass=CommandEnabler):
    '''
messages are:
1: command index
2: message size
n: message

codecs can encode/decode messages
'''
    def __init__(self):
        super().__init__()
        self.read, self.write = Pipe(duplex=True)
        # large lists append MUCH faster than large strings.
        self.buffer = bytearray()
    def send(self,command,message,finished=None):
        self.write.send_bytes(message)
    def check(self):
        b = self.read.recv_bytes()
        if not b:
            raise SystemExit('???')
        self.buffer.extend(b)
        while self.buffer:
            size = self.buffer[:2]
            size = size[0] << 8 + size[1]
            if size > len(self.buffer) - 2: return

            message = self.buffer[2:2+size]
            # python has odd splicing syntax
            del self.buffer[:2+size]

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
