from .things import Tag
from . import danbooru
from . import derpibooru
from . import furaffinity
from . import inkbunny
from . import rule34
from . import sofurry
from . import weasyl
from . import pixiv
from . import flickr
from . import zerochan
from ..parse import registerFinder as register

import re

register("www.zerochan.net",
        {'extract': zerochan.extract})

register("furry.booru.org",
        {'extract': danbooru.extract,
         'tags': [Tag('booru','furry')]})

register(re.compile("wildcritters\..*"),
        {'extract': danbooru.extract,
         'tags': ['wildcritters'],
         'normalize': danbooru.normalize},
        name="wildcritters")

register(re.compile("e621\..*"),
        {'extract': danbooru.extract,
         'tags': ['e621'],
         'normalize': danbooru.normalize},
        name="e621")

register("mspabooru.com",
        {'extract': danbooru.extract,
         'tags': ['mspaint'],
         'normalize': danbooru.normalize})

register("bronibooru.com",
        {'extract': danbooru.extract,
            'normalize': danbooru.normalize,
            'tags': ['pony','bronibooru','booru']})

register("www.bronibooru.com",
        {'extract': danbooru.extract,
            'normalize': danbooru.normalize,
            'tags': ['pony','bronibooru','booru']})

register(re.compile("twentypercentcooler\..*"),
        {'extract': danbooru.extract,
         'tags': ['twentypercentcooler','pony'],
         'normalize': danbooru.normalize},
        name="twentypercentcooler")

register(re.compile(".*furaffinity.net"),
        {'extract': furaffinity.extract,
         'tags': ['furaffinity'],
         'normalize': furaffinity.normalize},
        name="furaffinity")

register(re.compile(".*inkbunny.net"),
        {'extract': inkbunny.extract,
         'tags': ['inkbunny']},
        name="inkbunny")

register('rule34.xxx',
        {'extract': rule34.extract,
            'tags': ['rule34']})

register(re.compile('.*sofurry.com'),
        {'extract': sofurry.extract,
            'tags': ['sofurry']},
        name="sofurry")

register(re.compile('.*weasyl.com'),
        {'extract': weasyl.extract,
            'normalize': danbooru.normalize,
            'tags': ['weasyl']},
        name="weasyl")

register('derpibooru.org',
        {'extract': derpibooru.extract,
            'normalize': derpibooru.normalize,
            'tags': ['derpibooru','pony']})

register('derpiboo.ru',
        {'extract': derpibooru.extract,
            'normalize': derpibooru.normalize,
            'tags': ['derpibooru','pony']})

""" sigh...
register('www.pixiv.net',
        {'extract': pixiv.extract,
            'tags':['pixiv','japan']})
"""

tags = ['flickr','photo']
register('flickr.com',
        {'extract': flickr.extract,
            'tags':tags})
register('www.flickr.com',
        {'extract': flickr.extract,
            'tags':tags})
