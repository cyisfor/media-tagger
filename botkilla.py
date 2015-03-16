import random,time
from array import array

def dorp(a):
    # should be printable, biased towards low, but above 32
    a.extend(
        chr(int(random.random()**3*10000+32)) \
        for i in range(random.randint(100,200)))

def generateBody(a):
    # arrayifying this shaves off a whole 3ms :p
    a.extend('<!DOCTYPE html><html><head><title>')
    dorp(a)
    a.extend('''</title></head>'
<body><p>''')
    for link in range(random.randint(100,200)):
        if random.randrange(0,2)==0:
            a.extend("</p><p>")
        if random.randrange(0,10)==0:
            a.extend("<hr/>")
        if random.randrange(0,6):
            a.extend('\n')
        a.extend('<a href="/art/')
        dorp(a)
        a.extend('/secrets.html">')
        dorp(a)
        a.extend('</a>\n')
    a.extend('</p></body></html>')

def generate(date):
    a = array('u')
    generateBody(a)
    body = a.tounicode().encode('utf-8')    
    head = b'\r\n'.join((
        b'HTTP/1.1 200 OK',
        b'Content-Type: text/html; charset=utf-8',
        b'Date: '+date.encode(),
        b'Server: Apache',
        b'Content-Length: '
    ))
    return (head + b'0\r\n\r\n',
            head + str(len(body)).encode() + b'\r\n\r\n' + \
            body)

    
class BotHelper:
    lastBot = None
    messages = None
    def select(self,date,ip):
        if self.lastBot is None or time.time() - self.lastBot < 100:
            self.messages = [generate(date) for i in range(0x20)]
            self.lastBot = time.time()
        return random.sample(self.messages,1)[0]

def stresstest():
    print('started at',time.time())
        
    start = time.time()
    for i in range(0x20):
        generate('sometime')
    end = time.time()
    print('generated in',end-start)
    # this will take up 1% of the computer's brain time:
    print('recommended generation interval is ',int(100*(end-start)))

if __name__ == '__main__':
    stresstest()
else:
    import sys
    sys.modules[__name__] = BotHelper()
