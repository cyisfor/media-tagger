import db,withtags,filedb,tags,merge
from PIL import Image,ImageOps
import os,gc
from functools import lru_cache

@lru_cache(0x100)
def prepareImage(ai):
    a = os.path.join(filedb.base,'image','{:x}'.format(ai))

    a = Image.open(a)
    w,h = a.size
    if w > 0x200 or h > 0x200:
        w = min(w,0x200)
        h = min(h,0x200)
        a.resize((w,h))
    a = a.convert('RGB')
    a = ImageOps.equalize(a)
    return a.histogram(),a.getdata()

def getit(a):
    ai =  a[0]
    def check():
        return prepareImage(ai)

    aw = db.c.execute('SELECT width,height FROM images WHERE id = $1',(a[0],))
    return a[0],a[1],aw,check

def compare(a,b):
    if a[1] != b[1]: return
    if a[2] != b[2]: return

    ai = a[0]
    bi = b[0]

    a = a[3]() 
    b = b[3]()

    if a != b: return

    print('equal {:x} {:x}'.format(ai,bi))
    raise SystemExit
    merge.merge(ai,bi)

for thing1 in db.c.execute('SELECT images.id,type,width,height FROM images, media where images.id = media.id AND images.id < 375675 order by images.id desc'):
    print('1',thing1[0],thing1[1])
    gc.collect()
    width = thing1[2]
    height = thing1[3]
    thing1 = getit(thing1)
    if not thing1[2]: continue
    tests = db.c.execute('SELECT images.id,type FROM images, media WHERE images.id = media.id and images.id > $1 AND images.width = $2 AND images.height = $3 LIMIT 1000',(thing1[0],width,height))
    print(len(tests))
    for thing2 in tests:
        thing2 = getit(thing2)
        if not thing2[2]: continue
        compare(thing1,thing2)
