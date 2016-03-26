import syspath
import dbqueue

if __name__ == '__main__':
    import sys
    import io
    inp = io.TextIOWrapper(sys.stdin.buffer,encoding='utf-8')
    for line in inp:
        dbqueue.enqueue(line.strip())
    import parse
