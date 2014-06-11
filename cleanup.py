import filedb
import os,stat,sys

lastStat = None
def status(s):
    global lastStat
    s = str(s)
    sys.stdout.write('\r')
    sys.stdout.write(s)
    if lastStat is not None and len(s) < lastStat:
        sys.stdout.write(' '*(lastStat-len(s)))
    lastStat = len(s)
    sys.stdout.flush()
spaceReserved = {
        'thumb': 512*1024**2,
        'resized': 64*1024**2
}

pbuf = bytearray(0x1000)

for tempcategory in ('thumb','resized'):
    print(tempcategory)
    top = os.path.join(filedb.base,tempcategory).encode('utf-8')
    files = []
    pbuf[:len(top)] = top
    pbuf[len(top)] = os.sep.encode('utf-8')[0]
    for n in os.listdir(top):
        pbuf[len(top)+1:] = n
        st = os.stat(pbuf[:len(top)+1+len(n)])
        files.append((top,n,st.st_size,st.st_atime))
    files.sort(key=lambda e: -e[3]) # newest first

    space = spaceReserved[tempcategory]
    for top,n,size,atime in files:
        if space <= 0:
            status(space)
            os.remove(os.path.join(top,n))
        else:
            status(n)
            space -= size
    print('')
