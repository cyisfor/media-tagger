#/usr/bin/python3

import pymagic,os
from mimetypes import guess_extension

guesser = None
def init():
    global guesser
    guesser = pymagic.magic_open(pymagic.MAGIC_COMPRESS|pymagic.MAGIC_MIME|pymagic.MAGIC_CONTINUE|pymagic.MAGIC_PRESERVE_ATIME|pymagic.MAGIC_ERROR)

    compiled = False
    for database in (os.environ.get("MAGIC"),"/usr/share/file/misc/magic","/etc/magic"):
        if database:
            if os.path.exists(database+'.mgc'):
                compiled = True
                database = database + '.mgc'
                break
            elif os.path.exists(database): break
    else:
        raise RuntimeError("Couldn't find a magic database!")

    if compiled:
        database = database.encode('utf-8')
    else:
        base = os.path.basename(database)+'.mgc'
        if not os.path.exists(base):
            pymagic.magic_compile(guesser,database)
            database = base.encode('utf-8')

    pymagic.magic_load(guesser,database)

def guess_type_raw(data):
    if not guesser: init()
    if isinstance(data,str):
        return pymagic.magic_file(guesser,data.encode('utf-8'))
    elif isinstance(data,bytes):
        return pymagic.magic_buffer(guesser,data,len(data))
    elif isinstance(data,int):
        return pymagic.magic_descriptor(guesser,data)
    elif hasattr(data,'fileno'):
        return pymagic.magic_descriptor(guesser,data.fileno())

def guess_type(data):
    return guess_type_raw(data).decode('utf-8').split('; charset=')

if __name__=='__main__':
    import sys
    print(repr(guess_type(sys.argv[1])))
