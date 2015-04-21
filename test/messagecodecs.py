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
            assert v == codec.decode(m)
    def makenum(i):
        if i < 2: return i
        return random.randint(i,1000000)
    def makestr(i):
        if i == 0x3:
            return str(chr(0) * 100)
        return str(chr(random.randrange(0x100)) for b in range(i)))
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
    print(m)
    print('all tests passed')
    
if __name__ == '__main__':
    main()
