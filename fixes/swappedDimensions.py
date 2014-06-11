import create,filedb
import db

def getit(offset):
    return db.c.execute("SELECT media.id,width,height FROM images INNER JOIN media ON images.id = media.id ORDER BY media.added DESC OFFSET $1 LIMIT 1",(offset,))[0]

Fuzzy = []

def samewidth(offset):
    image,width,height = getit(offset)
    if width == height: return Fuzzy # don't want a false positive here
    animated,owidth,oheight = create.openImage(filedb.imagePath(image))[0]
    return width == owidth

toohigh = 5000
while True:
    if samewidth(toohigh) is True: 
        break
    print('toohigh',toohigh)
    toohigh *= 2

toolow = 0
while toolow + 1 < toohigh:
    print(toolow,toohigh)
    offset = int((toohigh+toolow)/2)
    while True:
        check = samewidth(offset)
        if check is not Fuzzy: break
        offset += 1
    if check is True:
        print('toohigh',toohigh)
        toohigh = offset
    elif check is False:
        print('toolow',toolow)
        toolow = offset

image,wid,hei = getit(toolow)

db.c.execute('UPDATE images SET width = height, height = width WHERE id >= $1',(image,))
print('Fixed ',toolow,'images')
