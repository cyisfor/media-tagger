import random
def dorp1():
    for i in range(random.randint(100,200)):
        # should be printable, biased towards low, but above 32
        yield chr(int(random.random()**3*10000+32))
    def dorp():
        return ''.join(dorp1())

def generateBody():
    yield '<!DOCTYPE html><html><head><title>'+dorp()+'''</title></head>
<body><p>'''
    for link in range(random.randint(100,200)):
        if random.randrange(0,2)==0:
            yield "</p><p>"
        if random.randrange(0,10)==0:
            yield "<hr/>"
        if random.randrange(0,6):
            yield '\n'
        yield '<a href="/art/'+dorp()+'/secrets.html">'+dorp()+'</a>\n'
    yield '</p></body></html>'

def generate(date):
    body = ', '.join(generateBody()).encode('utf-8')
    head = b'\r\n'.join((
        b'HTTP/1.1 200 OK',
        b'Content-Type: text/html; charset=utf-8',
        b'Date: '+date.encode()
        b'Server: Apache'))
    return (head + b'\r\nContent-Length: 0' + b'\r\n\r\n',
            head + b'\r\nContent-Length: '+str(len(body)).encode() + b'\r\n\r\n' + \
            body)

    
class BotHelper:
    lastBot = None
    messages = None
    def select(self):
        if self.lastBot is None or time.time() - self.lastBot < 100:
            self.messages = [generate() for i in range(10)]
            self.lastBot = time.time()
        return random.sample(self.messages,1)[0]
