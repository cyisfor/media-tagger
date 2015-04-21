#!/usr/bin/env pypy
import message
import random
def main():
    c = message.codecs
    m = bytearray()
    def check(codec,valgen):
        for i in range(0x1000):
            v = valgen(i)
            codec.encode(m,v)
            result = codec.decode(m)
            assert v == result, 'expected {} got {}'.format(repr(v),repr(result))
    def makenum(i):
        if i < 2: return i
        return random.randint(i,1000000)
    def makestr(i):
        if i == 0x3:
            return str(chr(0) * 100)
        s = ''.join(chr(random.randrange(0x10000)) for b in range(i&0xff))
        # strings can't be more than 0xff BYTES long (in utf-8)
        # if you keep within 0-0x80 characters (7-bit) you get 0xff characters
        # 0x80-0x800 eat 2 bytes though, 0x800->0x8000 eat 3, etc
        s = s.encode('utf-8',errors='replace')[:0xff]
        s = s.decode('utf-8',errors='ignore')
        return s
    check(c.num,makenum)
    check(c.str,makestr)
    assert not m, "bytes leftover?"
    def clearer(f):
        def wrapper(i):
            del m[:]
            return f(i)
        return wrapper
    check(c.one.num,clearer(makenum))
    check(c.one.str,clearer(makestr))
    print('all tests passed')
    
if __name__ == '__main__':
    main()
