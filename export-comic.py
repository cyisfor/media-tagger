import comic,info,db
from replacer import replacerFile as replace

import dirty.html as d

import sys,os
oj = os.path.join

c = int(sys.argv[1],0x10)
dest = sys.argv[2]

try:
    os.mkdir(dest)
except OSError: pass

def makePage(*content,head=(),title='???'):
    return str(d.html(d.head(d.title(title),*head),
                  d.body(content))).encode('utf-8')

def makeLink(which):
    return '{:x}.html'.format(which)

class Book:
    which = 0
    def __init__(self,pages,title,description,sources,tags):
        self.pages = pages
        self.title = title
        self.description = description
        self.tags = tags
        self.index = []
    def advance(self,which,mediumf,tags):
        self.index.append((mediumf,tags))
        link = makeLink(which)
        head = []
        links = []
        if which > 0:
            prev = makeLink(which-1)
            head.append(d.link(rel="prev",href=prev))
            links.append(d.a("Previous",href=prev))
        if which < self.pages:
            next = makeLink(which-1)
            head.append(d.link(rel="next",href=next))
            links.append(d.a("Next",href=next))
        links.append(d.a("Contents",href="./"))
        with replace(oj(dest,link)) as out:
            out.write(makePage(d.p(d.a(d.img(src=mediumf),href=mediumf)),
                               d.p(*links),
                               d.p("Tags: ",", ".join(tags)),
                               head=head,
                               title="{} page {:x}".format(
                                   self.title,which)))
    def commit(self):
        index = [d.a(d.img(
            src=image[0],title=", ".join(image[1])),href=makeLink(which)) for which,image in enumerate(self.index)]
        with replace(oj(dest,"index.html")) as out:
            out.write(makePage(
                d.h1(self.title),
                d.p(*index),
                d.p(self.description),
                d.p(", ".join(self.tags)),
                title=self.title))

book = Book(comic.pages(c),*comic.findInfoDerp(c)[0])
            
for which in range(book.pages):
    medium = comic.findMediumDerp(c,which)
    type = db.execute("SELECT type FROM media WHERE id = $1",(medium,))
    print(which,medium,type)
    mediumf = '{:x}.{}'.format(medium,type.split('/')[-1])
    shutil.copyfileobj(filedb.mediaPath(medium),oj(dest,mediumf))
    book.advance(which,mediumf,[r[0] for r in info.tagsFor(medium)])
book.commit()
