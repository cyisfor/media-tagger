import sys
sys.path.insert(0,'derp')
from itertools import chain

import re
rc = re.compile

alnum = rc('(?u)\w')
space = rc('(?u)\s')
dolla = '$'
parens = ('{}','()','[]')
escape = '\\'

matchparen = dict((p[1],p[0]) for p in parens)

oparens = set(p[0] for p in parens)
cparens = set(p[1] for p in parens)

class Thingy(str):
    def __repr__(self):
        return '<'+self.__class__.__name__+' '+repr(str(self))+'>'

class Space(Thingy): pass
class Other(Thingy): pass
class Quote(Thingy): pass
class Oparen(Thingy): pass
class Cparen(Thingy): pass
class Escape(Thingy): pass
class Name(Thingy): pass

class GotToken(Exception):
    def __init__(self,token):
        self.token = token

class Tokens:
    pos = 0
    c = None
    cc = None
    def __init__(self,inp):
        self.inp = inp
        c = inp.read(2)
        if c is None:
            self.next = lambda state,count: self.stop()
        self.c = c[0]
        self.cc = c[1]
        self.buf = []
    def stop(self):
        raise StopIteration
    def __iter__(self): return self
    def __next__(self):
        try:
            return self.readToken()
        except GotToken as e:
            return e.token
    nextToken = None
    def readToken(self):
        if self.nextToken:
            nt = self.nextToken
            del self.nextToken
            return nt
        def check(res):
            def decorator(f):
                if res:
                    if self.buf:
                        nt = Other(self.commit())
                        self.nextToken = f()(self.commit())
                        raise GotToken(nt)
                    else:
                        raise GotToken(f()(self.commit()))
            return decorator
        while True:
            @check(space.match(self.c))
            def eat():
                while space.match(self.readNext()):
                    pass
                return Space
            @check(dolla == self.c)
            def eat():                
                while alnum.match(self.readNext()):
                    pass
                return Quote
            @check('"' == self.c)
            def eat():
                self.readNext()
                return Quote
            @check("'" == self.c)
            def eat():
                self.readNext()
                return Quote
            @check(escape == self.c)
            def eat():
                self.readNext()
                return Escape
            @check(self.c in oparens)
            def eat():
                self.readNext()
                return Oparen
            @check(self.c in cparens)
            def eat():
                self.readNext()
                return Cparen
            @check(self.c == '-' and self.cc == '-')
            def eat():
                while self.readNext() != '\n':
                    pass
                return Comment
            @check(alnum.match(self.c))
            def eat():
                while alnum.match(self.readNext()):
                    pass
                return Name
            self.readNext()
    def readNext(self):
        # read the next character into self.c and return it.
        # goes into self.c for backtracking
        # self.cc for backtracking twice, for -- :(
        if self.cc:
            # don't read if not self.cc because that means EOF
            self.cc = self.inp.read(1)
        self.buf.append(self.c)
        self.c = self.cc
        if not self.c:
            raise StopIteration
        return self.c
    def commit(self):
        buf = ''.join(self.buf)
        self.buf[:] = ()
        return buf

def expect(what,tok):
    assert isinstance(tok,what)
    return tok

def parse(inp):
    tokens = Tokens(inp)
    parens = []
    quotes = []
    results = {}
    cur = []
    def eatSpace():
        tok = next(tokens)
        if isinstance(tok,Space):
            return next(tokens)
        return tok
    try:
        while True:
            tok = eatSpace()
            name = expect(Name,tok)
            for tok in tokens:
                if isinstance(tok,Oparen):
                    parens.append(tok)
                    break
                expect(Space,tok)
            for tok in tokens:
                cur.append(tok)
                if quotes:
                    if isinstance(tok,Quote) and tok == quotes[-1]:
                        quotes.pop(-1)
                else:
                    if isinstance(tok,Oparen):
                        parens.append(tok)
                    elif isinstance(tok,Cparen) and matchparen[tok] == parens[-1]:
                        parens.pop(-1)
                if not (quotes or parens): break
            results[name] = ''.join(cur[:-1])
            cur[:] = ()
    except StopIteration:
        return results
def derp():
    for k,v in parse(sys.stdin).items():
        print('um',k)
        print(repr(v))
    raise SystemExit

if __name__ == '__main__':
    import sys
    for name,value in parse(sys.stdin).items():
        print(name)
        print('-'*60)
        print(value)
