def popnum(message):
    size = message.pop(0)
    l = message[:size]
    del message[:size]
    sum = 0
    for i in l:
        sum = sum << 8 + i
    return sum

def pushnum(message,i):
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
    arg = message[:size]
    del message[:size]
    return bytes(*arg).decode('utf-8')
    
def pushstr(message,s):
    b = s.encode('utf-8')
    message.append(len(b))
    message.extend(b)

class MessageProcess(Process):
    commands = ()
    def __init__(self):
        super().__init__()
        self.read, self.write = Pipe(duplex=True)
        # large lists append MUCH faster than large strings.
        self.buffer = bytearray()
        self.rcommands = dict((v,i) for i,v in enumerate(self.commands))
    def send(self,command,message,finished=None):
        command = self.rcommands[command]
        length = len(message) + 1 # for command
        message[0:0] = (length >> 8, length & 0xff, command)
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

            self.commands[message.pop(0)](message)
