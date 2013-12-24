import syspath
import dbqueue

if __name__ == '__main__':
    import sys
    for line in sys.stdin:
        dbqueue.enqueue(line.strip())
