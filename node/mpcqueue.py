#!/usr/bin/env pypy

# implement a multiprocess queue (of limited size)
# using a semaphore, and a shared memory area.

import ctypes as c

class Thingy(c.Union):
    _fields_ = [("s",c.c_char_p),
                ("i",c.c_int)];

CHAR,INT,QUEUE = range(2)
        
class Item(c.Structure):
    _fields_ = [("data",Thingy),
                ("type",c.c_ubyte)]

Item._fields_.append(("next",c.POINTER(Item)))

class Queue(c.Structure)
    _fields_ = [("head",Item),
                ("tail",Item),
                ("mem")]

QueueP = c.POINTER(Queue)

# to push, if need space, just ftruncate and mremap
# keep queue,privateQueueSize, and when locking it,

# if queue size > privateQueueSize, mremap b/c another
# process added stuff to the end.

# to pop from the queue you......... uh....
# copy back and truncate, if it gets too big? 8/

Thingy._fields_.append(("q",c.POINTER(QueueP)))

def push(queue,item):
    assert isinstance(item,bytes) # can do int, str, or (int,str,...)
    assert(isinstance(queue,QueueP))
    
    
