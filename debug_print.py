from __future__ import print_function

import traceback
oldprint = print

def debug_print(*a,**kw):
    tb = traceback.extract_stack(limit=2)
    name,line,func,text = tb[-2]
    oldprint('{}:{}({})'.format(name,line,func),end=' ')
    return oldprint(*a,**kw)

print = debug_print

def test():
    print("hi")

if __name__ == '__main__':
    test()
