QUOTE,OPAREN,CPAREN,ESCAPE,SPACE = range(5)
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
    while True:
        c = inp.read(1)
        if not c: break
        if c in {' ','\t'}:
            yield SPACE,c
        if c == '\\':
            yield ESCAPE,inp.read(1)
        elif c in {'{','(','['}:
            if buf:
                yield buf,buf
            yield OPAREN,c
        elif c in {'}',')',']'}:
            if buf:
                yield buf,buf
            yield CPAREN,c
        elif c in {'"',"'"}:
            yield QUOTE,c
        elif c == "$":
            yield DOLLA,DOLLA
        elif c == '-':
            nc = inp.read(1)
            if not nc: break
            if nc == '-':
                if buf:
                    yield buf,buf
                yield COMMENT,COMMENT
            else:
                buf += c + nc
        elif c == '\n':
            if buf:
                yield buf,buf
            yield NL,NL
        else:
            buf += c

REDO,IGNORE,COMMIT = range(3)

# syntax name { ... } name { ... } yields name,statement pairs

def parse(inp):
    inComment = False
    gettingName = True
    eatingSpace = True
    seekDolla = False
    parens = []
    quotes = []
    value = []
    def commitValue():
        nonlocal value
        print('yay commit',value)
        s = ''.join(value)
        value.clear()
        return s
    tee = open('sofar.log','wt')
    def check(token,lit):
        tee.write(lit)
        nonlocal inComment,eatingSpace,seekDolla

        if eatingSpace:
            if token is not SPACE:
                eatingSpace = False
                return REDO
            return IGNORE

        if gettingName:
            if token is OPAREN or token is SPACE:
                if token is OPAREN:
                    parens.append(lit)
                    eatingSpace = True
                return COMMIT                
            return
        
        if inComment:
            if token is NL:
                inComment = False
            return
        
        if seekDolla:
            if token is DOLLA:
                if quotes and quotes[-1] == buf:
                    quotes.pop()
                else:
                    quotes.append(commitValue())
                seekDolla = False
            return
        
        if quotes:
            if token is QUOTE:
                if quotes and quotes[-1] == lit:
                    quotes.pop()
                else:
                    quotes.append(lit)
            elif token is DOLLA:
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
                seekDolla = True                
            return
    name = None
    for token,lit in tokens(inp):
        action = check(token,lit)
        while action is REDO:
            action = check(token,lit)
        if action is COMMIT:
            if name is None:
                name = commitValue()
                gettingName = False
            else:
                yield name,commitValue()
                name = None
                gettingName = True
        if action is not IGNORE:
            print('append',lit)
            value.append(lit)

if __name__ == '__main__':
    import sys
    for name,value in parse(sys.stdin):
        print(name)
        print('-'*60)
        print(value)
