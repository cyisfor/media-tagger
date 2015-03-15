QUOTE,OPAREN,CPAREN,ESCAPE,SPACE = range(5)
NL = '\n'
COMMENT = '--'
DOLLA = '$'
SEMICOLON = ';'

def tokens(inp):
    buf = ''
    while True:
        c = inp.read(1)
        if not c: break
        if c in {' ','\t'}:
            yield SPACE,c
        if c == '\\':
            yield ESCAPE,inp.read(1)
        elif c in {'{','(','[','<'}:
            if buf:
                yield buf,buf
            yield OPAREN,c
        elif c in {'}',')',']','>'}:
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

REDO,IGNORE = range(2)

# syntax name { ... } name { ... } yields name,statement pairs

def parse(inp):
    inQuote = False
    inComment = False
    gettingName = True
    eatingSpace = True
    parens = []
    quotes = []
    name = ''
    value = []
    def commitValue():
        nonlocal value
        s = ''.join(value)
        value.clear()
        return s
    def check(token,lit):
        nonlocal inQuote,inComment,gettingName,eatingSpace,name

        if eatingSpace:
            if token is not SPACE:
                eatingSpace = False
                return REDO
            return IGNORE

        if gettingName:
            if token is OPAREN or token is SPACE:
                if token is OPAREN:
                    parens.push(lit)
                    eatingSpace = True
                gettingName = False
                name = commitValue()
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
                    quotes.push(commitValue())
                seekDolla = False
            return
        
        if quotes:
            if token is QUOTE:
                if quotes and quotes[-1] == lit:
                    quotes.pop()
                else:
                    quotes.push(info[0])
            elif token is DOLLA:
                seekDolla = True
            # ignore braces inside quotes, even mismatched ones
            return
        
        if parens:
            if token is OPAREN:
                parens.push(lit)
            elif token is CPAREN:
                op = parens.pop()
                assert op == lit
                if not parens:
                    # yay finished
                    yield name,commitValue()
                    name = ''
                    gettingName = True
            elif token is QUOTE:
                quotes.push(lit)
            elif token is COMMENT:
                inComment = True
            elif token is DOLLA:
                seekDolla = True                
            return
    for token,lit in tokens(inp):
        action = check(token,lit)
        while action is REDO:
            action = check(token,lit)
        if action is not IGNORE:
            value.append(lit)

if __name__ == '__main__':
    import sys
    for name,value in parse(sys.stdin):
        print(name)
        print('-'*60)
        print(value)
