import comic,db

from itertools import count
import os,glob,sys
oj = os.path.join

which = count(0)

c = int(sys.argv[1],0x10)
place = sys.argv[2]
for i in count(0):
    for j in count(0):
        id = "{:x}.{:x}".format(i,j)
        print(id)
        try:
            path = glob.glob(oj(place,id+"*"))[0]
        except IndexError:
            if j == 0: raise SystemExit
            break
        m = db.execute('SELECT id FROM media WHERE sources @> array(SELECT id FROM filesources WHERE path = $1)',(path,))[0][0]
        comic.findMedium(c,next(which),m)
