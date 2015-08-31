import comic,info
import dirty as d

import sys,os

c = int(sys.argv[1],0x10)
dest = sys.argv[2]

def makePage(*content,head=(),title='???'):
    return d.html(d.head(d.title(title),*head),
                  d.body(content))

def makeLink(which):
    return '{:x}.html'.format(which)

class Book:
    which = 0
    def __init__(self,title,description,tags):
        self.title = title
        self.description = description
        self.tags = tags
        self.index = []
    def advance(self,which,medium,tags):
        self.index.append((medium,tags))
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
            out.write(makePage(d.p(d.a(href=medium,d.img(src=medium))),
                               *((d.p(*links),) if links else ()),
                               d.p("Tags: ",", ".join(tags))
                               head=head,
                               title="{} page {:x}".format(
                                   self.title,which)).encode('utf-8'))
    def commit():
        index = [d.a(href=makeLink(which),d.img(
            src=image[0],title=", ".join(image[1]))) for which,image in enumerate(self.index)]
        with replace(oj(dest,"index.html")) as out:
            out.write(makePage(
                d.h1(self.title),
                d.p(*index),
                d.p(self.description)
                d.p(", ".join(self.tags))
                title=self.title))
            
for which in range(comic.pages(c)):
    medium = comic.findMedium(c,which)
    book.advance(which,medium,[r[0] for r in info.tagsFor(medium)])
book.commit()
