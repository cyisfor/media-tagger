#!/usr/bin/env python3

import time

import syspath
from favorites.parseBase import parse,ParseError
from favorites import parsers

if __name__ == '__main__':
    import select
    import sys,io
    if len(sys.argv)>1:
        parse(sys.argv[1])
    else:
        sys.stdin = io.TextIOWrapper(sys.stdin.detach(),'utf-8')
        for line in sys.stdin:
            print('parsing',line.encode('utf-8'))
            try: parse(line.strip())
            except ParseError: pass
            except Exception as e:
                print(e)
                time.sleep(3)
