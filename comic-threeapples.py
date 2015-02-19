# mehhhhh

import db

import re

pagepattern = re.compile('page-([0-9]+)')

class Source:
    def __init__(self,id,uri):
        self.id = id
        self.uri = uri
    def __str__(self):
        return 'Source('+self.uri+')'

class Image:
    def __init__(self,id):
        self.id = id
        self.sources = [Source(*row) for row in db.execute('SELECT id,uri FROM urisources WHERE id IN (SELECT unnest(sources) FROM media WHERE id = $1)',(self.id,))]
        self.key = self.getkey()
    def getkey(self):
        for source in self.sources:
            match = pagepattern.search(source.uri)
            if match:
                return int(match.group(1))
        raise RuntimeError("No idea for which page is",self)
    def __str__(self):
        return "Image("self.id+','+self.sources+')'

images = [Image(id) for id in db.execute("SELECT neighbors FROM tags INNER JOIN things ON tags.id = things.id WHERE name = $1",('three apples',))[0][0]]

images.sort(key=lambda image: image.key)


