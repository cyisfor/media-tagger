CSI = b'\x1b['

memo = {}
def escape(*codes):
    codes = (str(code) for code in codes)
    if codes in memo:
        return memo[codes]
    ret = CSI+';'.join(codes).encode()+b'm'
    memo[codes] = ret
    return ret

bold = 1
derpbold = bold
underline=24
reset = escape(0)

colors = dict((v,i) for i,v in enumerate([
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

def color(name,bg=None,styles=()):
    if bg:
        codes = (colors[name]+30,colors[bg]+40) + styles
    else:
        codes = (colors[name]+30,) + styles
    return escape(*codes)

def fg(r,g,b):
    return escape(38,2,r+0x10,g+0x10,b+0x10)
def bg(r,g,b):
    return escape(48,2,r+0x10,g+0x10,b+0x10)

def test():
    import sys,random,os
    if 'nobold' in os.environ:
        styles = ()
    else:
        styles = (bold,)
    rcolor = random.sample(tuple(colors.keys()),1)[0]
    rcolor = color(rcolor,styles=styles)
    sys.stdout.buffer.write(
        rcolor+b'==base=='+reset+b'\n')
    
    for n,v in sorted(colors.items(),key=lambda pair: (pair[1],pair[0])):
        sys.stdout.buffer.write(
            color(n,styles=styles)+n.encode()+reset+b'\n')

    for r in range(0,217,36):
        for g in range(0,217,36):
            for b in range(0,217,36):
                sys.stdout.buffer.write(
                    fg(r,g,b)+bg(int(g/2),int(b/2),int(r/2))+'({},{},{})'.format(r,g,b).encode())
        sys.stdout.buffer.write(b'\n')


if __name__ == '__main__':
    test()	
