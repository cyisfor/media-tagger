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

def derp():
    tokens = Tokens(sys.stdin)
    parens = []
    quotes = []
    while True:
        tok = None
        for tok in tokens:
            if not isinstance(tok,Space): break
        name = expect(Name,tok)
        for tok in tokens:
            if isinstance(tok,Oparen):
                parens.append(tok)
                break
            expect(Space,tok)
        for tok in tokens:
            print('parens',len(parens),parens[-1],type(tok),tok)
            if isinstance(tok,Oparen):
                parens.append(tok)
            elif isinstance(tok,Cparen) and matchparen[tok] == parens[-1]:
                parens.pop(-1)
                break
        
        print('got',name)
derp()
raise SystemExit

lepl.core.config.factory(TokenFactory())
raise SystemExit()
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
