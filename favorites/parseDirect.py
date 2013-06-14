#!/usr/bin/env python3
import syspath
from parseBase import parse
import parsers

if __name__ == '__main__':
    import select
    import sys
    if len(sys.argv)>1:
        parse(sys.argv[1])
    else:
        for line in sys.stdin:
            parse(line.strip())
