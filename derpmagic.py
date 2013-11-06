#/usr/bin/python3

import magic,os,threading
from mimetypes import guess_extension

class MyGuesser(magic.Magic):
    def __init__(self,magic_file):
        self.cookie = magic.magic_open(magic.MAGIC_COMPRESS|magic.MAGIC_MIME|magic.MAGIC_CONTINUE|magic.MAGIC_PRESERVE_ATIME|magic.MAGIC_ERROR|magic.MAGIC_MIME_ENCODING)
        # lolololo
        magic.magic_load(self.cookie,magic_file)
        self.thread = threading.currentThread()

guesser = None
def init():
    global guesser
    compiled = False
    for database in (os.environ.get("MAGIC"),"/usr/share/file/misc/magic","/etc/magic"):
        if database:
            if os.path.exists(database+'.mgc'):
                compiled = True
                break
            elif os.path.exists(database): break
    else:
        raise RuntimeError("Couldn't find a magic database!")

    if not compiled:
        base = os.path.basename(database)+'.mgc'
        if not os.path.exists(base):
            magic.magic_compile(guesser.cookie,database)
            database = base

    print("loading "+database)
    guesser = MyGuesser(database)

def guess_type_raw(data):
    if not guesser: init()
    if isinstance(data,str):
        return guesser.from_file(data)
    elif isinstance(data,bytes):
        return guesser.from_buffer(data,len(data))
    elif isinstance(data,int):
        return magic.libmagic.magic_descriptor(guesser.cookie,data)
    elif hasattr(data,'fileno'):
        return guess_type_raw(data.fileno())

def guess_type(data):
    return guess_type_raw(data).decode('utf-8').split('; charset=')

if __name__=='__main__':
    import sys
    print(repr(guess_type(sys.argv[1])))
