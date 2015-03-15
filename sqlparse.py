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
    while True:
        c = inp.read(1)
        if not c: break
        gotit = None
        if c in {' ','\t'}:
            gotit = SPACE,c
        elif c == '\\':
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
            
        if gotit:
            if buf:
                yield STUFF,buf
                buf = ''
            yield gotit


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
        s = ''.join(value)
        value.clear()
        return s
    tee = open('sofar.log','wt')
    def check(token,lit):
        tee.write(lit)
        nonlocal inComment,eatingSpace,seekDolla

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
                seekDolla = False
            elif token is SPACE:
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
            print('beep')
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

        if token is OPAREN:
            parens.append(lit)
            eatingSpace = True
            return IGNORE
            
    name = None
    for token,lit in tokens(inp):
        print('toke',parens,lit)
        action = check(token,lit)
        while action is REDO:
            action = check(token,lit)
        if action is COMMIT:
            eatingSpace = True
            if name is None:
                name = commitValue()
                gettingName = False
                print('name is',name)
            else:
                yield name,commitValue().rstrip()
                print('valllu')
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
