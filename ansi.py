CSI = b'\x1b['

bold = CSI+b'1m'
derpbold = bold
reset = CSI+b'0m'

def makecolor(i):
    return CSI+bytes(str(i+30))+b'm'

colors = dict((v,makecolor(i)) for i,v in enumerate([
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'grey',
    'ehunno',
    'white']))

colors['default'] = colors['white']

def color(name,bold=False):
    ret = colors[name]
    if bold:
        return ret + derpbold
    return ret

def test():
    import sys,random,os
    rcolor = random.sample(tuple(colors.values()),1)[0]

    dobold = not 'nobold' in os.environ
    if dobold:
        dobold = bold
    else:
        dobold = b''
    sys.stdout.buffer.write(
        rcolor+dobold+b'==base=='+reset+b'\n')
    
    for n,v in sorted(colors.items(),key=lambda pair: (pair[1],pair[0])):
        sys.stdout.buffer.write(
            rcolor+v+dobold+n.encode()+reset+b'\n')        

if __name__ == '__main__':
    test()    
