# mehhhhh

import db,comic

import re

pagepattern = re.compile('page-([0-9]+)')

class Source:
    def __init__(self,id,uri):
        self.id = id
        self.uri = uri
    def __repr__(self):
        return 'Source('+self.uri+')'
    def __str__(self):
        return self.__repr__()

class Image:
    def __init__(self,id):
        self.id = id
        self.sources = [Source(*row) for row in db.execute('SELECT id,uri FROM urisources WHERE id IN (SELECT unnest(sources) FROM media WHERE id = $1)',(self.id,))]
        self.key = self.getkey()
    def getkey(self):        
        if self.id == 0x5c599:
            return 43
        elif self.id == 0x69c00:
            # shove in mid
            return -5           #
        elif self.id == 0x69c15:
            return -7
        elif self.id == 0x69c16:
            return -6
        elif self.id == 0x69c2f:
            return -9
        elif self.id == 0x69c2d:
            return -8 # at end plz
        elif self.id == 0x69bfa:
            return -4
        elif self.id == 0x69b85:
            return -3
        elif self.id == 0x650ab:
            return -2
        elif self.id == 0x650ac:
            return -1
        for source in self.sources:
            match = pagepattern.search(source.uri)
            if match:
                return int(match.group(1))
        print('uh',self.__repr__())            
        raise RuntimeError("No idea for which page is",self)
    def __repr__(self):
        return "Image({:x}".format(self.id)+','+','.join(str(s) for s in self.sources)+')'

images = [Image(row[0]) for row in db.execute("SELECT media.id FROM media INNER JOIN things ON media.id = things.id WHERE neighbors @> array(SELECT id FROM tags WHERE name = $1)",('general:three apples',))]

images.sort(key=lambda image: image.key)

c = comic.findComicByTitle('Three Apples',lambda: "A Great Three-Part Comedy-Adventure Serial MLP Fancomic With a Combination of Black Comedy, Absurd Humor and Some Third Thing That Everybody Likes")
for which,image in enumerate(images):
    comic.findMedium(c,which,image.id)
    db.execute('SELECT setComicPage($1,$2,$3)',(medium,c,which))
    print('image',which,image.id,image.key)


