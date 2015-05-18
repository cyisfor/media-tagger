import sys
sys.path.insert(0,'derp')
import lepl as l
import lepl.core.config
from itertools import chain

import re
rc = re.compile

alnum = rc('(?u)\w')
space = rc('(?u)\s')
dolla = '$'
parens = ('{}','()','[]')
escape = '\\'

oparens = set(p[0] for p in parens)
cparens = set(p[1] for p in parens)

class Thingy(str):
    def __repr__(self):
        return '<'+self.__class__.__name__+' '+repr(str(self))+'>'

class Space(Thingy): pass
class Other(Thingy): pass
class Dolla(Thingy): pass
class Oparen(Thingy): pass
class Cparen(Thingy): pass
class Escape(Thingy): pass

class Stream:
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
    def key(self, state, other):
        return HashKey(hash(state) ^ hash(self.c+self.cc) ^ hash(other) ^ hash(self.pos),(self.pos,self.c,self.cc,hash(other)))
    def kargs(self, state, prefix='', kargs=None):
        return {'pos': self.pos, 'c': self.c, 'cc': self.cc}
    def debug(self,state):
        return 'uh'
    def empty(self):
        return self.c is None
    def len(self, state):
        raise TypeError
    def next(self, state, count=1):
        start = state
        if start != self.pos:
            if start != self.inp.seek(start):
                raise StopIteration
        self.pos = start
        tokens = [self.readToken() for i in range(count)]
        new_stream = (self.pos, self)
        return (tokens,new_stream)
    def readToken(self):
        while True:
            if space.match(self.c):
                if self.buf: return Other(self.commit())
                while space.match(self.readNext()):
                    pass
                return Space(self.commit())
            elif dolla == self.c:
                if self.buf: return Other(self.commit())
                while not dolla == self.readNext():
                    pass
                return Dolla(self.commit())
            elif escape == self.c:
                self.readNext()
                return Escape(self.commit())
            elif self.c in oparens:
                if self.buf: return Other(self.commit())
                self.readNext()
                return Oparen(self.commit())
            elif self.c in cparens:
                if obuf: return Other(''.join(obuf))
                self.readNext()
                return Cparen(self.commit())
            elif self.c in '-':
                if self.c2 == self.readNext():
                    if self.buf: return Other(self.commit())
                    while self.readNext() != '\n':
                        pass
                    return Comment(self.commit())
                else:
                    self.buf.extend('-',nc)
            else:
                self.readNext()
    def readNext(self):
        # read the next character into self.c and return it.
        # goes into self.c for backtracking
        # self.cc for backtracking twice, for -- :(
        self.buf.append(self.c)
        self.c = self.cc
        if not self.c:
            raise StopIteration
        if self.cc:
            # don't read if not self.cc because that means EOF
            self.cc = self.inp.read(1)
        return self.c
    def commit(self):
        buf = ''.join(self.buf)
        self.buf[:] = ()
        return buf

class TokenFactory:
    def from_file(self,inp):
        return Stream(inp)

def derp():
    derp = Stream(sys.stdin)
    pos = 0
    while True:
        try:
            stuff,(pos,derp) = derp.next(pos,3)
            print(stuff,pos,derp)
        except StopIteration: break
derp()

#lepl.config.factory(TokenFactory())



space = l.Token(space)
dolla = l.Token(dolla)
escape = l.Token(escape)
#parens = [(l.Token(l.Literal(s[0])),l.Token(l.Literal(s[1]))) for s in (
comment = l.Token(comment)
name = l.Token(alnum)

block = l.Delayed()
derp = []
for p in parens:
    derp.append(space[0:1] & p[0] & space[0:1] & block & space[0:1] & p[1] & space[0:1])
block += l.Or(*derp)

stmt = name & space[0:1] & parens[0][0] & block & parens[0][1] & space[0:1]

stmts = l.Star(stmt)

#print(repr(stmt))

def testTokens():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("test")
    import sys
    print(repr(dolla))

    print(dolla.match("$abcdefg$"))

    tokens = stmts.get_match_file()
    for token in tokens(sys.stdin):
        print(token)
    raise SystemExit
testTokens()

tokens = stmts.get_match_file()

REDO,IGNORE,COMMIT = range(3)

# syntax name { ... } name { ... } yields name,statement pairs

debugging = False

def derpyderp(f):
    def wrapper(token,lit):
        action = f(token,lit)
        if debugging:
            print(token,action,repr(lit))
        return action
    return wrapper


def parse(inp):
    inComment = False
    gettingName = True
    eatingSpace = True
    seekDolla = False
    parens = []
    quotes = []
    value = []
    beforeDolla = []
    def commitValue():
        nonlocal value
        s = ''.join(value)
        value[:] = ()
        return s
    @derpyderp
    def check(token,lit):
        nonlocal inComment,eatingSpace,seekDolla, beforeDolla
        if debugging:
            print('incom',inComment,eatingSpace,seekDolla,quotes,parens)
        if inComment:
            if token is NL:
                inComment = False
            if eatingSpace: return IGNORE
            return

        if eatingSpace:
            if token is COMMENT:
                inComment = True
            elif token not in {SPACE,NL}:
                eatingSpace = False
                inComment = False
                return REDO
            return IGNORE

        if gettingName:
            if token is OPAREN or token is SPACE:
                if token is OPAREN:
                    parens.append(lit)
                return COMMIT
            return

        if seekDolla:
            if token is DOLLA:
                v = commitValue()
                if quotes and quotes[-1] == v:
                    quotes.pop()
                else:
                    quotes.append(v)
                if beforeDolla:
                    value[:0] = beforeDolla
                    value.append(v)
                seekDolla = False
            elif token is not STUFF:
                # $1 is valid, despite $1___derp$ being a dollar quote...
                seekDolla = False
                return REDO
            return

        if quotes:
            if token is QUOTE:
                if quotes and quotes[-1] == lit:
                    quotes.pop()
                else:
                    quotes.append(lit)
            elif token is DOLLA:
                beforeDolla[:] = value
                value[:] = ()
                seekDolla = True
            # ignore braces inside quotes, even mismatched ones
            return

        if parens:
            if token is OPAREN:
                parens.append(lit)
            elif token is CPAREN:
                op = parens.pop()
                assert op == parenfor[lit], "{} != {}".format(op,lit)
                if not parens:
                    # yay finished
                    return COMMIT
            elif token is QUOTE:
                quotes.append(lit)
            elif token is COMMENT:
                inComment = True
            elif token is DOLLA:
                beforeDolla[:] = value
                value[:] = ()
                seekDolla = True
            return

        if token is OPAREN:
            parens.append(lit)
            eatingSpace = True
            return IGNORE

    name = None
    for token,lit in tokens(inp):
        action = check(token,lit)
        while action is REDO:
            action = check(token,lit)
        if action is COMMIT:
            eatingSpace = True
            if name is None:

                name = commitValue()
                gettingName = False
            else:
                yield name,commitValue().rstrip().rstrip(';')
                name = None
                gettingName = True
        elif action is not IGNORE:
            value.append(lit)

if __name__ == '__main__':
    import sys
    for name,value in parse(sys.stdin):
        print(name)
        print('-'*60)
        print(value)
