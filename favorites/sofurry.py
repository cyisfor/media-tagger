from .things import *
import re
import urllib.parse

def hasClass(c):
    def handler(e):
        return e == c
    return handler


def extract(doc):
    download = doc.find('a',id='sfDownload')
    if download:
        yield Image(download['href'])
    else:
        for img in doc.findAll('img'):
            if 'preview?' in img['src']:
                yield Image(img.parent['href'])
                break
        else:
            raise RuntimeError("Can't find an image...",doc)
    for tag in doc.findAll('a',{'class': 'sf-tag'}):
        href = tag.get('href')
        if href and 'search=%23' in href:
            yield Tag('general',urllib.parse.unquote(href.split('search=%23')[-1]))
    username = doc.find('span', hasClass('sf-username'))
    yield Tag('artist',username.contents[0])
