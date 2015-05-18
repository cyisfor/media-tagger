import lepl as l
import strings

alnum = l.Regexp('(?u)\w+')
spaces = l.Regexp('(?u)\s+')
newline = l.Token(l.Literal('\n'))
dolla = l.Literal('$')
dolla = l.Token(dolla&alnum[0:1]&dolla)
parens = [(l.Token(s[0]),l.Token(s[1])) for s in (
    '()','[]','{}')]
semicolon = l.Token(l.Literal(';'))
escape = l.Token(l.Literal('\\')&l.Any())
comment = l.Token(l.Literal('--')&l.Star(l.Any())&l.Literal('\n'))
name = l.Token(alnum)

block = l.Delayed()
block += Or(*((space[0:1]&p[0]&space[0:1]&block&space[0:1]&+p[1]&space[0:1]) for p in parens))
stmt = name & space[0:1] & parens[0] & block & parens[1]
QUOTE,OPAREN,CPAREN,ESCAPE,SPACE,STUFF = range(6)
NL = '\n'
COMMENT = '--'
DOLLA = '$'
SEMICOLON = ';'

parenfor = {
    '}': '{',
    ')': '(',
    ']': '[',
    }

def tokens(inp):
    buf = ''
    last = STUFF
    c = inp.read(1)
    if not c: return
    while True:
        gotit = None
        if c in {' ','\t','\n'}:
            gotit = SPACE,c
        if c == '\\':
            gotit = ESCAPE,inp.read(1)
        elif c in {'{','(','['}:
            gotit = OPAREN,c
        elif c in {'}',')',']'}:
            gotit = CPAREN,c
        elif c in {'"',"'"}:
            gotit = QUOTE,c
        elif c == "$":
            gotit = DOLLA,DOLLA
        elif c == '-':
            nc = inp.read(1)
            if not nc: break
            if nc == '-':
                gotit = COMMENT,COMMENT
            else:
                buf += c + nc
        elif c == '\n':
            gotit = NL,NL
        else:
            buf += c
        
        if not gotit:
            c = inp.read(1)
        else:
            if buf:
                yield STUFF,buf
                buf = ''
            mode,c = gotit
            if mode == SPACE:
                buf.append(c)
                while True:
                    c = inp.read(1)
                    if c in {' ','\t','\n'}:
                        buf.append(c)
                    else:
                        yield SPACE,buf
                        buf = ''
                        break
            elif mode == DOLLA:
                while True:
                    c = inp.read(1)
                    if c == DOLLA:
                        yield DOLLA,buf
                        buf = ''
                        break
                    else:
                        buf.append(c)
            else:
                yield gotit
                c = inp.read(1)


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
