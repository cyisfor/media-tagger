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
            
def parse(inp):
    inQuote = False
    inComment = False
    gettingName = True
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
        nonlocal inQuote,inComment,gettingName,name,value
        if token is ESCAPE:
            value.append(lit)
            
        if gettingName:
            if token is OPAREN or token is SPACE:
                if token is OPAREN:
                    parens.push(lit)
                    eatingSpace = True
                gettingName = False
                name = commitValue()
            return
        
        if eatingSpace:
            if token is not SPACE:
                eatingSpace = False
                return REDO
            return IGNORE
        
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
                parens.push(info[0])
                buf += info[0]
            elif token is CPAREN:
                op = parens.pop()
                assert op == info[0]
            elif token is QUOTE:
                quotes.push(info[0])
            else:
                buf += token
                if token is COMMENT:
                    inComment = True
                elif token is DOLLA:
                    seekDolla = True
                
            continue

        if token is OPAREN:
            parenLevel += 1
        elif token is 
