import comic,info,db,filedb
from replacer import replacerFile as replace

from itertools import repeat
import dirty.html as d
import shutil
import sys,os
oj = os.path.join

c = int(sys.argv[1],0x10)
dest = sys.argv[2]

try:
    os.mkdir(dest)
except OSError: pass

style = """
.page {
    max-width: 95%;
}

body {
    text-align: center;
}"""

with replace(oj(dest,"style.css")) as out:
    out.write(style.encode('utf-8'))

def makePage(*content,head=(),title='???'):
    return str(d.html(d.head(d.title(title),d.link(rel='stylesheet',href='style.css'),*head),
                  d.body(content))).encode('utf-8')

def makeLink(which):
    return '{:x}.html'.format(which)

def makeThumb(which):
    return '{:x}-thumb.jpg'.format(which)

def cleanupTag(tag):
    if tag.startswith('general:'): return tag[len('general:'):]
    return tag

class Book:
    which = 0
    def __init__(self,pages,title,description,sources,tags):
        self.pages = pages
        self.title = title
        self.description = description
        self.tags = tags
        self.index = []
    def advance(self,which,mediumf,tags):
        tags=[cleanupTag(tag) for tag in tags]
        self.index.append(tags)
        link = makeLink(which)
        head = []
        links = []
        if which > 0:
            prev = makeLink(which-1)
            head.append(d.link(rel="prev",href=prev))
            links.append(d.a("Previous",href=prev))
        next = "./index.html"
        if which < self.pages-1:
            next = makeLink(which+1)
            head.append(d.link(rel="next",href=next))
            links.append(d.a("Next",href=next))
        links.append(d.a("Contents",href="./index.html"))
        with replace(oj(dest,link)) as out:
            out.write(makePage(d.p(d.a(d.img(class_='page',src=mediumf),href=next)),
                               d.p(*zip(links,repeat(' '))),
                               d.p("Tags: ",", ".join(tags)),
                               head=head,
                               title="{} page {:x}".format(
                                   self.title,which)))
    def commit(self):
        index = [d.a(d.img(
            src=makeThumb(which),title=", ".join(tags)),href=makeLink(which)) for which,tags in enumerate(self.index)]
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
    type = db.execute("SELECT type FROM media WHERE id = $1",(medium,))[0][0]
    print(which,medium,type)
    mediumf = '{:x}.{}'.format(which,type.split('/')[-1])
    shutil.copy2(filedb.mediaPath(medium),oj(dest,mediumf))
    shutil.copy2(filedb.thumbPath(medium),oj(dest,makeThumb(which)))
    book.advance(which,mediumf,[r[0] for r in info.tagsFor(medium)])
book.commit()
